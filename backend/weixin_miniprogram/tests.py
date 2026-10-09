"""
点名清单后端 API 测试。

覆盖 8 个端点的正常路径、校验分支与权限分支，重点是：
- 分享语义（white_list / permission / activity_type='public'）不要走样
- 登录接口不再清空已有头像/昵称
- 头像 URL 是绝对地址，且换头像后旧缓存失效
- 数值 key 排序、脏数据不崩

跑法：
    cd backend && python manage.py test weixin_miniprogram
"""

import base64
import os
import shutil
import tempfile
from unittest import mock

from django.conf import settings
from django.core.cache import cache
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.utils.functional import empty
from rest_framework.test import APITestCase

from .api_views import AvatarDecodeError, build_avatar_from_base64, get_avatar_url
from .models import Activities, WeixinUserInfo

BASE_DIR = settings.BASE_DIR

API = '/weixin-miniprogram/api'

# 1x1 透明 PNG，够 ImageField 落盘用
PNG_1X1 = (
    b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
    b'\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01'
    b'\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
)

APP_CREDENTIALS = override_settings(
    WEIXIN_MINIPROGRAM_APP_ID='wx-test-appid',
    WEIXIN_MINIPROGRAM_APP_SECRET='test-appsecret',
)


def items(*names):
    """构造 activity_items，key 从 '1' 开始。"""
    return {str(i + 1): {'name': name, 'status': '', 'operator': ''}
            for i, name in enumerate(names)}


def member(weixin_id, permission=''):
    return {'weixin_id': weixin_id, 'avatar_url': '', 'permission': permission}


def make_activity(creator='u_creator', title='活动A', activity_items=None,
                  activity_white_list=None, activity_type=''):
    return Activities.objects.create(
        creator_weixin_id=creator,
        creator_weixin_name='创建者',
        activity_type=activity_type,
        activity_title=title,
        activity_items=(items('张三', '李四') if activity_items is None
                        else activity_items),
        white_list=([member(creator, 'creator')] if activity_white_list is None
                    else activity_white_list),
    )


def fake_wechat_response(payload, status_code=200):
    response = mock.Mock()
    response.status_code = status_code
    response.json.return_value = payload
    return response


class RollCallAPITestCase(APITestCase):
    """
    公共基座：隔离媒体目录 + 清空缓存。

    头像会真的写文件，必须落到项目内的临时目录，不能污染 backend/avatars/。
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._media_dir = tempfile.mkdtemp(prefix='.test-media-', dir=BASE_DIR)
        cls._media_override = override_settings(MEDIA_ROOT=cls._media_dir)
        cls._media_override.enable()
        # FileSystemStorage.location 是 cached_property，覆盖 MEDIA_ROOT 后
        # 必须把已缓存的 storage 实例丢掉，否则还是写老目录。
        default_storage._wrapped = empty

    @classmethod
    def tearDownClass(cls):
        cls._media_override.disable()
        default_storage._wrapped = empty
        shutil.rmtree(cls._media_dir, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        super().setUp()
        cache.clear()

    # ------------------------------------------------------------------
    # 工具方法
    # ------------------------------------------------------------------
    def login(self, code='code-1', openid='openid-1', avatar_name=None,
              nickname=None):
        """调用 /jscode2session/。avatar_name 非空时带一个上传文件。"""
        payload = {}
        if avatar_name:
            payload['avatar'] = SimpleUploadedFile(
                avatar_name, PNG_1X1, content_type='image/png')
        if nickname is not None:
            payload['nickname'] = nickname
        if code is not None:
            payload['code'] = code

        with mock.patch('weixin_miniprogram.api_views.requests.get',
                        return_value=fake_wechat_response({'openid': openid})):
            return self.client.post(f'{API}/jscode2session/', payload,
                                    format='multipart')

    def create_activity(self, creator='u_creator', title='活动A',
                        activity_items=('张三', '李四'), activity_type=''):
        return self.client.post(f'{API}/activities/', {
            'creator_weixin_id': creator,
            'activity_title': title,
            'activity_items': list(activity_items),
            'activity_type': activity_type,
        }, format='json')

    def fetch(self, activity_id, weixin_id):
        return self.client.get(f'{API}/activities/{activity_id}/',
                               {'weixin_id': weixin_id})

    def set_item_status(self, activity_id, item_id, weixin_id, status):
        return self.client.put(f'{API}/activities/{activity_id}/items/{item_id}/',
                               {'weixin_id': weixin_id,
                                'activity_item_status': status},
                               format='json')


# ======================================================================
# 1. 登录 / 头像
# ======================================================================

@APP_CREDENTIALS
class JSCode2SessionTests(RollCallAPITestCase):

    def test_missing_code_returns_400(self):
        response = self.client.post(f'{API}/jscode2session/', {}, format='multipart')
        self.assertEqual(response.status_code, 400)
        self.assertIn('code', response.json()['error'])
        self.assertEqual(WeixinUserInfo.objects.count(), 0)

    @override_settings(WEIXIN_MINIPROGRAM_APP_ID='',
                       WEIXIN_MINIPROGRAM_APP_SECRET='')
    def test_missing_app_credentials_returns_400(self):
        response = self.client.post(f'{API}/jscode2session/', {'code': 'x'},
                                    format='multipart')
        self.assertEqual(response.status_code, 400)

    def test_wechat_http_error_returns_400(self):
        with mock.patch('weixin_miniprogram.api_views.requests.get',
                        return_value=fake_wechat_response({}, status_code=502)):
            response = self.client.post(f'{API}/jscode2session/', {'code': 'x'},
                                        format='multipart')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(WeixinUserInfo.objects.count(), 0)

    def test_wechat_response_without_openid_returns_400(self):
        with mock.patch('weixin_miniprogram.api_views.requests.get',
                        return_value=fake_wechat_response({'errcode': 40029})):
            response = self.client.post(f'{API}/jscode2session/', {'code': 'x'},
                                        format='multipart')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(WeixinUserInfo.objects.count(), 0)

    def test_login_creates_user_and_returns_absolute_avatar_url(self):
        response = self.login(openid='openid-1', avatar_name='a.png')

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body['weixin_id'], 'openid-1')
        self.assertTrue(
            body['avatar_url'].startswith('http://testserver/avatars/weixin/openid-1/'),
            body['avatar_url'])

        user = WeixinUserInfo.objects.get(weixin_id='openid-1')
        self.assertTrue(user.avatar.name.startswith('avatars/weixin/openid-1/'))
        # 文件真的落在被覆盖后的 MEDIA_ROOT 下
        self.assertTrue(
            os.path.exists(os.path.join(settings.MEDIA_ROOT, user.avatar.name)))

    def test_login_twice_is_idempotent(self):
        self.login(openid='openid-1', avatar_name='a.png')
        self.login(openid='openid-1', avatar_name='b.png')
        self.assertEqual(WeixinUserInfo.objects.filter(weixin_id='openid-1').count(), 1)

    def test_login_without_avatar_keeps_existing_avatar(self):
        self.login(openid='openid-1', avatar_name='a.png')
        first_name = WeixinUserInfo.objects.get(weixin_id='openid-1').avatar.name

        response = self.login(openid='openid-1')  # 不带头像

        self.assertEqual(response.status_code, 200)
        user = WeixinUserInfo.objects.get(weixin_id='openid-1')
        self.assertTrue(user.avatar, '不带头像登录不应该把已有头像清空')
        self.assertEqual(user.avatar.name, first_name)
        self.assertTrue(os.path.exists(os.path.join(settings.MEDIA_ROOT, first_name)))
        self.assertTrue(response.json()['avatar_url'].endswith(first_name))

    def test_login_without_avatar_on_new_user_returns_empty_avatar_url(self):
        response = self.login(openid='openid-fresh')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['avatar_url'], '')
        self.assertEqual(WeixinUserInfo.objects.get(weixin_id='openid-fresh').avatar, '')

    def test_login_replaces_avatar_and_deletes_old_file(self):
        self.login(openid='openid-2', avatar_name='a.png')
        old_name = WeixinUserInfo.objects.get(weixin_id='openid-2').avatar.name
        old_path = os.path.join(settings.MEDIA_ROOT, old_name)

        response = self.login(openid='openid-2', avatar_name='b.png')
        new_name = WeixinUserInfo.objects.get(weixin_id='openid-2').avatar.name

        self.assertNotEqual(old_name, new_name)
        self.assertFalse(os.path.exists(old_path), '换头像应删掉旧文件')
        self.assertTrue(os.path.exists(os.path.join(settings.MEDIA_ROOT, new_name)))
        self.assertIn(os.path.basename(new_name), response.json()['avatar_url'])

    def test_login_invalidates_cached_avatar_url(self):
        # 1) 首次登录并落一个头像
        first = self.login(openid='openid-3', avatar_name='a.png').json()
        # 2) 建一个自己的活动，让头像 URL 进缓存
        self.create_activity(creator='openid-3', title='我的活动')
        cache_key = 'avatar_url_openid-3'
        self.assertTrue(cache.get(cache_key), '创建活动应该填充了头像缓存')

        # 3) 换头像
        second = self.login(openid='openid-3', avatar_name='c.png').json()

        self.assertIsNone(cache.get(cache_key),
                          '换头像后旧的头像 URL 缓存必须失效')

        # 4) 重新取一次拿到的是新地址
        self.client.get(f'{API}/activities/', {'weixin_id': 'openid-3'})
        self.assertIn(os.path.basename(second['avatar_url']), cache.get(cache_key) or '')
        self.assertNotEqual(first['avatar_url'], second['avatar_url'])

    def test_login_does_not_clobber_nickname_when_absent(self):
        self.login(openid='openid-4', nickname='小明')
        self.assertEqual(WeixinUserInfo.objects.get(weixin_id='openid-4').nickname, '小明')

        self.login(openid='openid-4')  # 不再传 nickname

        self.assertEqual(WeixinUserInfo.objects.get(weixin_id='openid-4').nickname, '小明')

    def test_login_updates_nickname_when_provided(self):
        self.login(openid='openid-5', nickname='小明')
        self.login(openid='openid-5', nickname='小红')
        self.assertEqual(WeixinUserInfo.objects.get(weixin_id='openid-5').nickname, '小红')

    def test_login_returns_json(self):
        response = self.login(openid='openid-6')
        self.assertEqual(response['Content-Type'].split(';')[0], 'application/json')


# ======================================================================
# 1b. 登录：JSON + base64 头像通道
#
# 这条通道存在的唯一理由：wx.uploadFile 要「uploadFile 合法域名」，而那个列表可能
# 由第三方平台托管、开发者改不了。wx.request 用的是另一张白名单，一般已经配好。
# ======================================================================

@APP_CREDENTIALS
class JSCode2SessionBase64Tests(RollCallAPITestCase):

    def login_json(self, openid='openid-b64', avatar_bytes=None,
                   ext='jpeg', base64_value=None, code='code-json'):
        payload = {}
        if code is not None:
            payload['code'] = code
        if base64_value is not None:
            payload['avatar_base64'] = base64_value
            payload['avatar_ext'] = ext
        elif avatar_bytes is not None:
            payload['avatar_base64'] = base64.b64encode(avatar_bytes).decode('ascii')
            payload['avatar_ext'] = ext

        with mock.patch('weixin_miniprogram.api_views.requests.get',
                        return_value=fake_wechat_response({'openid': openid})):
            return self.client.post(f'{API}/jscode2session/', payload, format='json')

    def test_json_login_with_base64_avatar(self):
        response = self.login_json(openid='openid-b64', avatar_bytes=PNG_1X1, ext='png')

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body['weixin_id'], 'openid-b64')
        self.assertTrue(
            body['avatar_url'].startswith('http://testserver/avatars/weixin/openid-b64/'),
            body['avatar_url'])
        self.assertTrue(body['avatar_url'].endswith('.png'))

        user = WeixinUserInfo.objects.get(weixin_id='openid-b64')
        self.assertTrue(user.avatar.name.endswith('.png'))
        # 落盘的字节要和原始图片完全一致
        with open(os.path.join(settings.MEDIA_ROOT, user.avatar.name), 'rb') as handle:
            self.assertEqual(handle.read(), PNG_1X1)

    def test_json_login_without_avatar_is_allowed(self):
        response = self.login_json(openid='openid-b64-noavatar')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['avatar_url'], '')
        self.assertEqual(WeixinUserInfo.objects.get(weixin_id='openid-b64-noavatar').avatar, '')

    def test_json_login_empty_base64_is_treated_as_no_avatar(self):
        response = self.login_json(openid='openid-b64-empty', base64_value='')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['avatar_url'], '')

    def test_json_login_keeps_existing_avatar_when_absent(self):
        self.login(openid='openid-b64-keep', avatar_name='a.png')
        before = WeixinUserInfo.objects.get(weixin_id='openid-b64-keep').avatar.name

        response = self.login_json(openid='openid-b64-keep')

        self.assertEqual(response.status_code, 200)
        user = WeixinUserInfo.objects.get(weixin_id='openid-b64-keep')
        self.assertEqual(user.avatar.name, before)
        self.assertTrue(response.json()['avatar_url'].endswith(before))

    def test_json_login_replaces_existing_avatar(self):
        self.login(openid='openid-b64-swap', avatar_name='a.png')
        before = WeixinUserInfo.objects.get(weixin_id='openid-b64-swap').avatar.name

        response = self.login_json(openid='openid-b64-swap', avatar_bytes=PNG_1X1, ext='png')
        after = WeixinUserInfo.objects.get(weixin_id='openid-b64-swap').avatar.name

        self.assertNotEqual(before, after)
        self.assertFalse(os.path.exists(os.path.join(settings.MEDIA_ROOT, before)))
        self.assertIn(os.path.basename(after), response.json()['avatar_url'])

    def test_json_login_invalidates_cached_avatar_url(self):
        first = self.login_json(openid='openid-b64-cache',
                                avatar_bytes=PNG_1X1, ext='png').json()
        self.create_activity(creator='openid-b64-cache', title='我的活动')
        cache_key = 'avatar_url_openid-b64-cache'
        self.assertTrue(cache.get(cache_key))

        second = self.login_json(openid='openid-b64-cache',
                                 avatar_bytes=PNG_1X1, ext='jpeg').json()

        self.assertIsNone(cache.get(cache_key))
        self.assertNotEqual(first['avatar_url'], second['avatar_url'])

    def test_json_login_rejects_malformed_base64(self):
        response = self.login_json(openid='openid-b64-bad', base64_value='这不是 base64!!')

        self.assertEqual(response.status_code, 400)
        self.assertIn('base64', response.json()['error'])
        self.assertEqual(WeixinUserInfo.objects.count(), 0)

    def test_json_login_rejects_oversized_avatar(self):
        with mock.patch('weixin_miniprogram.api_views.MAX_AVATAR_BYTES', 10):
            response = self.login_json(openid='openid-b64-big', avatar_bytes=PNG_1X1)

        self.assertEqual(response.status_code, 400)
        self.assertIn('过大', response.json()['error'])

    def test_json_login_falls_back_to_jpeg_for_unknown_extension(self):
        response = self.login_json(openid='openid-b64-ext',
                                   avatar_bytes=PNG_1X1, ext='exe')

        self.assertEqual(response.status_code, 200)
        user = WeixinUserInfo.objects.get(weixin_id='openid-b64-ext')
        self.assertTrue(user.avatar.name.endswith('.jpeg'))

    def test_json_login_accepts_extension_with_leading_dot(self):
        self.login_json(openid='openid-b64-dot', avatar_bytes=PNG_1X1, ext='.png')
        user = WeixinUserInfo.objects.get(weixin_id='openid-b64-dot')
        self.assertTrue(user.avatar.name.endswith('.png'))

    def test_json_login_still_requires_code(self):
        response = self.client.post(f'{API}/jscode2session/', {}, format='json')
        self.assertEqual(response.status_code, 400)

    def test_multipart_channel_still_works(self):
        # 向后兼容：旧客户端还在用 multipart，不能被这次改动弄坏
        response = self.login(openid='openid-both', avatar_name='a.png')

        self.assertEqual(response.status_code, 200)
        user = WeixinUserInfo.objects.get(weixin_id='openid-both')
        self.assertTrue(user.avatar.name.endswith('.png'))

    def test_build_avatar_from_base64_returns_none_without_payload(self):
        self.assertIsNone(build_avatar_from_base64({}))
        self.assertIsNone(build_avatar_from_base64({'avatar_ext': 'png'}))

    def test_build_avatar_from_base64_builds_uploaded_file(self):
        uploaded = build_avatar_from_base64({
            'avatar_base64': base64.b64encode(PNG_1X1).decode('ascii'),
            'avatar_ext': 'gif',
        })

        self.assertEqual(uploaded.name, 'avatar.gif')
        self.assertEqual(uploaded.content_type, 'image/gif')
        self.assertEqual(uploaded.read(), PNG_1X1)

    def test_build_avatar_from_base64_raises_on_garbage(self):
        with self.assertRaises(AvatarDecodeError):
            build_avatar_from_base64({'avatar_base64': '***'})

    def test_build_avatar_from_base64_treats_empty_string_as_absent(self):
        # 空字符串等于「本次没传头像」，不该报错，也不该把已有头像清掉
        self.assertIsNone(build_avatar_from_base64({'avatar_base64': ''}))


# ======================================================================
# 2. 活动列表
# ======================================================================

class ActivityListTests(RollCallAPITestCase):

    def test_requires_weixin_id(self):
        response = self.client.get(f'{API}/activities/')
        self.assertEqual(response.status_code, 400)

    def test_splits_my_shared_and_public(self):
        make_activity(creator='me', title='我创建的')
        mine_public = make_activity(creator='me', title='我创建的公共',
                                    activity_type='public')
        make_activity(creator='other', title='共享给我的',
                      activity_white_list=[member('other', 'creator'), member('me')])
        make_activity(creator='other', title='别人的私有')
        make_activity(creator='other', title='公共的', activity_type='public')

        body = self.client.get(f'{API}/activities/', {'weixin_id': 'me'}).json()

        self.assertEqual([a['activity_title'] for a in body['my']], ['我创建的'])
        self.assertEqual([a['activity_title'] for a in body['shared']], ['共享给我的'])
        self.assertCountEqual([a['activity_title'] for a in body['public']],
                              ['我创建的公共', '公共的'])
        self.assertNotIn(mine_public.id, [a['id'] for a in body['my']])

    def test_shared_match_is_exact_not_substring(self):
        # 'u1' 不能因为 'u10' 在白名单里就被判成共享
        make_activity(creator='other', title='给 u10 的',
                      activity_white_list=[member('other', 'creator'), member('u10')])

        body = self.client.get(f'{API}/activities/', {'weixin_id': 'u1'}).json()

        self.assertEqual(body['shared'], [])

    def test_list_response_shape_is_stable(self):
        make_activity(creator='me', title='活动A')
        body = self.client.get(f'{API}/activities/', {'weixin_id': 'me'}).json()

        self.assertEqual(set(body.keys()), {'my', 'shared', 'public'})
        self.assertEqual(
            set(body['my'][0].keys()),
            {'id', 'creator_weixin_id', 'creator_weixin_name', 'activity_title',
             'activity_items', 'activity_type', 'white_list'})

    def test_items_are_sorted_by_numeric_key(self):
        make_activity(creator='me',
                      activity_items={'10': {'name': 'J', 'status': '', 'operator': ''},
                                      '2': {'name': 'B', 'status': '', 'operator': ''},
                                      '1': {'name': 'A', 'status': '', 'operator': ''}})
        body = self.client.get(f'{API}/activities/', {'weixin_id': 'me'}).json()
        self.assertEqual(list(body['my'][0]['activity_items'].keys()), ['1', '2', '10'])

    def test_item_without_status_key_does_not_crash(self):
        make_activity(creator='me', activity_items={'1': {'name': '脏数据'}})
        response = self.client.get(f'{API}/activities/', {'weixin_id': 'me'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()['my'][0]['activity_items']['1']['operator_avatar_url'], '')

    def test_item_with_non_numeric_key_does_not_crash(self):
        make_activity(creator='me',
                      activity_items={'b': {'name': 'B', 'status': '', 'operator': ''},
                                      '1': {'name': 'A', 'status': '', 'operator': ''}})
        response = self.client.get(f'{API}/activities/', {'weixin_id': 'me'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['my'][0]['activity_items']), 2)


# ======================================================================
# 3. 创建活动
# ======================================================================

class ActivityCreateTests(RollCallAPITestCase):

    def test_requires_creator_title_and_items(self):
        for missing in ('creator_weixin_id', 'activity_title', 'activity_items'):
            payload = {'creator_weixin_id': 'me', 'activity_title': 'T',
                       'activity_items': ['A']}
            payload.pop(missing)
            with self.subTest(missing=missing):
                response = self.client.post(f'{API}/activities/', payload, format='json')
                self.assertEqual(response.status_code, 400)

    def test_rejects_non_list_items(self):
        response = self.client.post(f'{API}/activities/', {
            'creator_weixin_id': 'me',
            'activity_title': 'T',
            'activity_items': {'1': 'A'},
        }, format='json')
        self.assertEqual(response.status_code, 400)

    def test_creates_items_and_creator_white_list(self):
        response = self.create_activity(creator='me', title='活动A',
                                        activity_items=('张三', '李四'))

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body['activity_items'], {
            '1': {'name': '张三', 'status': '', 'operator': '', 'operator_avatar_url': ''},
            '2': {'name': '李四', 'status': '', 'operator': '', 'operator_avatar_url': ''},
        })
        self.assertEqual(body['white_list'][0]['weixin_id'], 'me')
        self.assertEqual(body['white_list'][0]['permission'], 'creator')

    def test_default_type_is_private(self):
        body = self.create_activity(creator='me').json()
        self.assertEqual(body['activity_type'], '')

    def test_can_create_public_activity(self):
        body = self.create_activity(creator='me', activity_type='public').json()

        self.assertEqual(body['activity_type'], 'public')
        self.assertEqual(Activities.objects.get(id=body['id']).activity_type, 'public')

    def test_empty_item_list_creates_empty_items(self):
        response = self.client.post(f'{API}/activities/', {
            'creator_weixin_id': 'me', 'activity_title': '空', 'activity_items': [],
        }, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['activity_items'], {})


# ======================================================================
# 4. 活动详情 / 改名 / 删除
# ======================================================================

class ActivityDetailTests(RollCallAPITestCase):

    def test_404_for_missing_activity(self):
        response = self.fetch(999999, 'me')
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()['error'], '活动不存在')

    def test_requires_weixin_id(self):
        activity = make_activity()
        response = self.client.get(f'{API}/activities/{activity.id}/')
        self.assertEqual(response.status_code, 400)

    def test_visitor_is_appended_to_white_list_as_visitor(self):
        activity = make_activity(creator='owner')
        response = self.fetch(activity.id, 'visitor')

        self.assertEqual(response.status_code, 200)
        activity.refresh_from_db()
        entries = {item['weixin_id']: item['permission'] for item in activity.white_list}
        self.assertEqual(entries, {'owner': 'creator', 'visitor': ''})
        self.assertEqual({item['weixin_id'] for item in response.json()['white_list']},
                         {'owner', 'visitor'})

    def test_visiting_twice_does_not_duplicate(self):
        activity = make_activity(creator='owner')
        self.fetch(activity.id, 'visitor')
        self.fetch(activity.id, 'visitor')

        activity.refresh_from_db()
        ids = [item['weixin_id'] for item in activity.white_list]
        self.assertEqual(ids.count('visitor'), 1)

    def test_creator_is_not_duplicated(self):
        activity = make_activity(creator='owner')
        self.fetch(activity.id, 'owner')

        activity.refresh_from_db()
        ids = [item['weixin_id'] for item in activity.white_list]
        self.assertEqual(ids.count('owner'), 1)


class ActivityUpdateTitleTests(RollCallAPITestCase):

    def test_requires_weixin_id_and_title(self):
        activity = make_activity(creator='owner')

        response = self.client.put(f'{API}/activities/{activity.id}/',
                                   {'activity_title': '新标题'}, format='json')
        self.assertEqual(response.status_code, 400)

        response = self.client.put(f'{API}/activities/{activity.id}/',
                                   {'weixin_id': 'owner'}, format='json')
        self.assertEqual(response.status_code, 400)

    def test_only_creator_can_rename(self):
        activity = make_activity(creator='owner',
                                 activity_white_list=[member('owner', 'creator'),
                                                      member('admin', 'admin')])
        response = self.client.put(f'{API}/activities/{activity.id}/',
                                   {'weixin_id': 'admin', 'activity_title': '新标题'},
                                   format='json')

        self.assertEqual(response.status_code, 403)
        activity.refresh_from_db()
        self.assertEqual(activity.activity_title, '活动A')

    def test_creator_can_rename(self):
        activity = make_activity(creator='owner')
        response = self.client.put(f'{API}/activities/{activity.id}/',
                                   {'weixin_id': 'owner', 'activity_title': '新标题'},
                                   format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['activity_title'], '新标题')
        activity.refresh_from_db()
        self.assertEqual(activity.activity_title, '新标题')


class ActivityDeleteTests(RollCallAPITestCase):

    def test_requires_weixin_id_and_source(self):
        activity = make_activity(creator='owner')

        response = self.client.delete(f'{API}/activities/{activity.id}/',
                                      {'source': 'my'}, format='json')
        self.assertEqual(response.status_code, 400)

        response = self.client.delete(f'{API}/activities/{activity.id}/',
                                      {'weixin_id': 'owner'}, format='json')
        self.assertEqual(response.status_code, 400)

    def test_rejects_unknown_source(self):
        activity = make_activity(creator='owner')
        response = self.client.delete(f'{API}/activities/{activity.id}/',
                                      {'weixin_id': 'owner', 'source': 'public'},
                                      format='json')
        self.assertEqual(response.status_code, 400)

    def test_creator_deletes_own_activity(self):
        activity = make_activity(creator='owner')
        response = self.client.delete(f'{API}/activities/{activity.id}/',
                                      {'weixin_id': 'owner', 'source': 'my'},
                                      format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['message'], '活动删除成功')
        self.assertFalse(Activities.objects.filter(id=activity.id).exists())

    def test_non_creator_cannot_delete_my(self):
        activity = make_activity(creator='owner',
                                 activity_white_list=[member('owner', 'creator'),
                                                      member('admin', 'admin')])
        response = self.client.delete(f'{API}/activities/{activity.id}/',
                                      {'weixin_id': 'admin', 'source': 'my'},
                                      format='json')

        self.assertEqual(response.status_code, 403)
        self.assertTrue(Activities.objects.filter(id=activity.id).exists())

    def test_shared_delete_only_removes_caller_from_white_list(self):
        activity = make_activity(creator='owner',
                                 activity_white_list=[member('owner', 'creator'),
                                                      member('guest')])
        response = self.client.delete(f'{API}/activities/{activity.id}/',
                                      {'weixin_id': 'guest', 'source': 'shared'},
                                      format='json')

        self.assertEqual(response.status_code, 200)
        activity.refresh_from_db()
        self.assertTrue(Activities.objects.filter(id=activity.id).exists())
        self.assertEqual([item['weixin_id'] for item in activity.white_list], ['owner'])

    def test_shared_delete_forbidden_for_outsider(self):
        activity = make_activity(creator='owner')
        response = self.client.delete(f'{API}/activities/{activity.id}/',
                                      {'weixin_id': 'stranger', 'source': 'shared'},
                                      format='json')
        self.assertEqual(response.status_code, 403)


# ======================================================================
# 5. 另存为我的
# ======================================================================

class ActivityCopyTests(RollCallAPITestCase):

    def test_requires_weixin_id(self):
        activity = make_activity(creator='owner')
        response = self.client.post(f'{API}/activities/{activity.id}/copy-to-my/',
                                    {}, format='json')
        self.assertEqual(response.status_code, 400)

    def test_404_for_missing_activity(self):
        response = self.client.post(f'{API}/activities/999999/copy-to-my/',
                                    {'weixin_id': 'me'}, format='json')
        self.assertEqual(response.status_code, 404)

    def test_copy_resets_item_state(self):
        activity = make_activity(
            creator='owner', title='原活动',
            activity_items={'1': {'name': '张三', 'status': 'completed',
                                  'operator': 'owner'},
                            '2': {'name': '李四', 'status': 'deleted',
                                  'operator': 'owner'}},
            activity_white_list=[member('owner', 'creator'), member('me')])

        response = self.client.post(f'{API}/activities/{activity.id}/copy-to-my/',
                                    {'weixin_id': 'me'}, format='json')
        self.assertEqual(response.status_code, 200)

        copy = Activities.objects.exclude(id=activity.id).get()
        self.assertEqual(copy.creator_weixin_id, 'me')
        self.assertEqual(copy.activity_title, '原活动')
        self.assertEqual(copy.activity_items, {
            '1': {'name': '张三', 'status': '', 'operator': ''},
            '2': {'name': '李四', 'status': '', 'operator': ''},
        })
        self.assertEqual(copy.white_list,
                         [{'weixin_id': 'me', 'avatar_url': '', 'permission': 'creator'}])

    def test_copy_of_public_activity_is_private(self):
        activity = make_activity(creator='owner', activity_type='public')
        self.client.post(f'{API}/activities/{activity.id}/copy-to-my/',
                         {'weixin_id': 'me'}, format='json')

        self.assertEqual(Activities.objects.get(creator_weixin_id='me').activity_type, '')

    def test_copy_returns_refreshed_lists(self):
        activity = make_activity(creator='owner')
        body = self.client.post(f'{API}/activities/{activity.id}/copy-to-my/',
                                {'weixin_id': 'me'}, format='json').json()

        self.assertEqual(set(body.keys()), {'my', 'shared', 'public'})
        self.assertEqual(len(body['my']), 1)
        self.assertEqual(body['my'][0]['activity_title'], '活动A')

    def test_copy_preserves_item_order(self):
        activity = make_activity(
            creator='owner',
            activity_items={str(i): {'name': f'第{i}人', 'status': '', 'operator': ''}
                            for i in range(1, 12)})
        self.client.post(f'{API}/activities/{activity.id}/copy-to-my/',
                         {'weixin_id': 'me'}, format='json')

        copy = Activities.objects.get(creator_weixin_id='me')
        self.assertEqual(list(copy.activity_items.keys()), [str(i) for i in range(1, 12)])


# ======================================================================
# 6. 白名单 / 管理员
# ======================================================================

class WhiteListTests(RollCallAPITestCase):

    def setUp(self):
        super().setUp()
        self.activity = make_activity(
            creator='owner',
            activity_white_list=[member('owner', 'creator'), member('guest')])

    def put(self, payload):
        return self.client.put(
            f'{API}/activities/{self.activity.id}/white_list/', payload, format='json')

    def test_requires_weixin_id(self):
        response = self.put({'white_list': {'weixin_id': 'guest', 'permission': 'admin'}})
        self.assertEqual(response.status_code, 400)

    def test_requires_white_list(self):
        response = self.put({'weixin_id': 'owner'})
        self.assertEqual(response.status_code, 400)

    def test_white_list_must_be_dict(self):
        response = self.put({'weixin_id': 'owner', 'white_list': []})
        self.assertEqual(response.status_code, 400)

    def test_missing_permission_returns_400_not_500(self):
        response = self.put({'weixin_id': 'owner',
                             'white_list': {'weixin_id': 'guest'}})

        self.assertEqual(response.status_code, 400)
        self.assertIn('permission', response.json()['error'])
        # 不能静默把管理员降级
        self.activity.refresh_from_db()
        self.assertEqual(self.activity.white_list[1]['permission'], '')

    def test_missing_weixin_id_in_entry_returns_400(self):
        response = self.put({'weixin_id': 'owner',
                             'white_list': {'permission': 'admin'}})
        self.assertEqual(response.status_code, 400)

    def test_invalid_permission_returns_400(self):
        response = self.put({'weixin_id': 'owner',
                             'white_list': {'weixin_id': 'guest',
                                            'permission': 'creator'}})

        self.assertEqual(response.status_code, 400)
        self.activity.refresh_from_db()
        self.assertEqual([item['permission'] for item in self.activity.white_list],
                         ['creator', ''])

    def test_only_creator_can_change_white_list(self):
        response = self.put({'weixin_id': 'guest',
                             'white_list': {'weixin_id': 'guest', 'permission': 'admin'}})

        self.assertEqual(response.status_code, 403)
        self.activity.refresh_from_db()
        self.assertEqual(self.activity.white_list[1]['permission'], '')

    def test_promote_existing_member_to_admin(self):
        response = self.put({'weixin_id': 'owner',
                             'white_list': {'weixin_id': 'guest', 'permission': 'admin'}})

        self.assertEqual(response.status_code, 200)
        entries = {item['weixin_id']: item['permission']
                   for item in response.json()['white_list']}
        self.assertEqual(entries['guest'], 'admin')
        self.activity.refresh_from_db()
        self.assertEqual(self.activity.white_list[1]['permission'], 'admin')

    def test_demote_admin_to_visitor(self):
        self.put({'weixin_id': 'owner',
                  'white_list': {'weixin_id': 'guest', 'permission': 'admin'}})
        response = self.put({'weixin_id': 'owner',
                             'white_list': {'weixin_id': 'guest', 'permission': ''}})

        entries = {item['weixin_id']: item['permission']
                   for item in response.json()['white_list']}
        self.assertEqual(entries['guest'], '')

    def test_appends_new_member(self):
        response = self.put({'weixin_id': 'owner',
                             'white_list': {'weixin_id': 'newbie',
                                            'permission': 'admin'}})

        self.assertEqual(response.status_code, 200)
        entries = {item['weixin_id']: item['permission']
                   for item in response.json()['white_list']}
        self.assertEqual(entries['newbie'], 'admin')


# ======================================================================
# 7. 事项的新增 / 重置
# ======================================================================

class ActivityItemsTests(RollCallAPITestCase):

    def setUp(self):
        super().setUp()
        self.activity = make_activity(
            creator='owner',
            activity_white_list=[member('owner', 'creator'), member('admin', 'admin')])

    def add(self, payload):
        return self.client.post(f'{API}/activities/{self.activity.id}/items/',
                                payload, format='json')

    def test_add_item_requires_fields(self):
        self.assertEqual(self.add({'activity_item_name': '王五'}).status_code, 400)
        self.assertEqual(self.add({'weixin_id': 'owner'}).status_code, 400)

    def test_only_creator_can_add_item(self):
        response = self.add({'weixin_id': 'admin', 'activity_item_name': '王五'})
        self.assertEqual(response.status_code, 403)

    def test_add_item_uses_next_numeric_key(self):
        response = self.add({'weixin_id': 'owner', 'activity_item_name': '王五'})

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(list(body['activity_items'].keys()), ['1', '2', '3'])
        self.assertEqual(body['activity_items']['3']['name'], '王五')

    def test_add_item_uses_max_key_not_count(self):
        self.activity.activity_items = {
            '1': {'name': 'A', 'status': '', 'operator': ''},
            '7': {'name': 'B', 'status': '', 'operator': ''}}
        self.activity.save()

        body = self.add({'weixin_id': 'owner', 'activity_item_name': 'C'}).json()

        self.assertIn('8', body['activity_items'])
        self.assertEqual(body['activity_items']['8']['name'], 'C')

    def test_add_item_to_empty_activity_starts_at_one(self):
        self.activity.activity_items = {}
        self.activity.save()

        body = self.add({'weixin_id': 'owner', 'activity_item_name': 'A'}).json()

        self.assertEqual(body['activity_items'],
                         {'1': {'name': 'A', 'status': '',
                                'operator': '', 'operator_avatar_url': ''}})

    def test_init_items_resets_status_and_operator(self):
        self.activity.activity_items = {
            '1': {'name': 'A', 'status': 'completed', 'operator': 'admin'},
            '2': {'name': 'B', 'status': 'deleted', 'operator': 'owner'},
        }
        self.activity.save()

        response = self.client.put(f'{API}/activities/{self.activity.id}/init-items/',
                                   {'weixin_id': 'owner'}, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['activity_items'], {
            '1': {'name': 'A', 'status': '', 'operator': '', 'operator_avatar_url': ''},
            '2': {'name': 'B', 'status': '', 'operator': '', 'operator_avatar_url': ''},
        })
        self.activity.refresh_from_db()
        self.assertEqual(self.activity.activity_items['1']['operator'], '')

    def test_init_items_requires_weixin_id(self):
        response = self.client.put(f'{API}/activities/{self.activity.id}/init-items/',
                                   {}, format='json')
        self.assertEqual(response.status_code, 400)

    def test_init_items_only_creator(self):
        response = self.client.put(f'{API}/activities/{self.activity.id}/init-items/',
                                   {'weixin_id': 'admin'}, format='json')
        self.assertEqual(response.status_code, 403)


# ======================================================================
# 8. 单条事项状态
# ======================================================================

class ActivityItemStatusTests(RollCallAPITestCase):

    def setUp(self):
        super().setUp()
        self.activity = make_activity(
            creator='owner',
            activity_items={'1': {'name': '张三', 'status': '', 'operator': ''}},
            activity_white_list=[member('owner', 'creator'),
                                 member('admin', 'admin'),
                                 member('guest')])

    def delete_item(self, item_id, weixin_id):
        return self.client.delete(
            f'{API}/activities/{self.activity.id}/items/{item_id}/',
            {'weixin_id': weixin_id}, format='json')

    def test_requires_weixin_id(self):
        response = self.client.put(
            f'{API}/activities/{self.activity.id}/items/1/',
            {'activity_item_status': 'completed'}, format='json')
        self.assertEqual(response.status_code, 400)

    def test_requires_status(self):
        response = self.client.put(
            f'{API}/activities/{self.activity.id}/items/1/',
            {'weixin_id': 'guest'}, format='json')
        self.assertEqual(response.status_code, 400)

    def test_rejects_invalid_status(self):
        response = self.set_item_status(self.activity.id, '1', 'guest', 'unknown')
        self.assertEqual(response.status_code, 400)

    def test_outsider_cannot_operate(self):
        response = self.set_item_status(self.activity.id, '1', 'stranger', 'completed')
        self.assertEqual(response.status_code, 403)

    def test_unknown_item_returns_404(self):
        response = self.set_item_status(self.activity.id, '99', 'guest', 'completed')
        self.assertEqual(response.status_code, 404)

    def test_guest_completes_item_and_records_operator(self):
        response = self.set_item_status(self.activity.id, '1', 'guest', 'completed')

        self.assertEqual(response.status_code, 200)
        item = response.json()['activity_items']['1']
        self.assertEqual(item['status'], 'completed')
        self.assertEqual(item['operator'], 'guest')

    def test_guest_can_undo_own_completion(self):
        self.set_item_status(self.activity.id, '1', 'guest', 'completed')
        response = self.set_item_status(self.activity.id, '1', 'guest', '')

        item = response.json()['activity_items']['1']
        self.assertEqual(item['status'], '')
        self.assertEqual(item['operator'], '')

    def test_delete_status_marks_item(self):
        response = self.set_item_status(self.activity.id, '1', 'guest', 'deleted')

        item = response.json()['activity_items']['1']
        self.assertEqual(item['status'], 'deleted')
        self.assertEqual(item['operator'], 'guest')

    def test_cannot_override_item_operated_by_someone_else(self):
        self.set_item_status(self.activity.id, '1', 'guest', 'completed')
        response = self.set_item_status(self.activity.id, '1', 'admin', 'completed')
        self.assertEqual(response.status_code, 400)

    def test_creator_can_override_any_item(self):
        self.set_item_status(self.activity.id, '1', 'guest', 'completed')
        response = self.set_item_status(self.activity.id, '1', 'owner', 'deleted')

        self.assertEqual(response.status_code, 200)
        item = response.json()['activity_items']['1']
        self.assertEqual(item['status'], 'deleted')
        self.assertEqual(item['operator'], 'owner')

    def test_delete_requires_weixin_id(self):
        response = self.client.delete(
            f'{API}/activities/{self.activity.id}/items/1/', {}, format='json')
        self.assertEqual(response.status_code, 400)

    def test_only_creator_can_delete_item_forever(self):
        response = self.delete_item('1', 'admin')

        self.assertEqual(response.status_code, 403)
        self.activity.refresh_from_db()
        self.assertIn('1', self.activity.activity_items)

    def test_creator_delete_item_forever(self):
        response = self.delete_item('1', 'owner')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['activity_items'], {})
        self.activity.refresh_from_db()
        self.assertEqual(self.activity.activity_items, {})

    def test_delete_unknown_item_returns_404(self):
        response = self.delete_item('99', 'owner')
        self.assertEqual(response.status_code, 404)


# ======================================================================
# 9. 模型 / 辅助函数
# ======================================================================

class ModelTests(RollCallAPITestCase):

    def test_last_modified_is_refreshed_on_save(self):
        activity = make_activity()
        original = activity.last_modified

        with mock.patch('weixin_miniprogram.models.current_timestamp',
                        return_value=original + 1000):
            activity.activity_title = '改个名'
            activity.save()

        activity.refresh_from_db()
        self.assertEqual(activity.last_modified, original + 1000)

    def test_weixin_user_info_str(self):
        user = WeixinUserInfo.objects.create(weixin_id='openid-x', nickname='小明')
        self.assertIn('openid-x', str(user))

    def test_activity_str(self):
        activity = make_activity(title='晨跑点名')
        self.assertIn('晨跑点名', str(activity))

    def test_get_avatar_url_returns_empty_for_unknown_user(self):
        self.assertEqual(get_avatar_url(None, 'nobody'), '')

    def test_get_avatar_url_returns_empty_for_user_without_avatar(self):
        WeixinUserInfo.objects.create(weixin_id='openid-noavatar')
        self.assertEqual(get_avatar_url(None, 'openid-noavatar'), '')

    def test_get_avatar_url_returns_empty_for_blank_id(self):
        self.assertEqual(get_avatar_url(None, ''), '')
