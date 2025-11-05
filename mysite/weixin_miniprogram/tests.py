from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Activities


class ActivitiesAPITestCase(APITestCase):

    def setUp(self):
        # 创建测试数据
        self.creator_weixin_id = 'creator_123'
        self.member_weixin_id = 'member_456'
        self.other_weixin_id = 'other_789'

        # 创建活动
        self.activity = Activities.objects.create(
            creator_weixin_id=self.creator_weixin_id,
            creator_weixin_name='创建者',
            activity_title='测试活动',
            activity_items={
                '1': {'name': '事项1', 'status': '', 'operator': ''},
                '2': {'name': '事项2', 'status': '', 'operator': ''}
            },
            white_list=[self.creator_weixin_id, self.member_weixin_id]
        )

        self.activity2 = Activities.objects.create(
            creator_weixin_id='other_creator',
            creator_weixin_name='其他创建者',
            activity_title='其他活动',
            activity_items={'1': {'name': '其他事项', 'status': '', 'operator': ''}},
            white_list=['other_creator']
        )

    def _log_test_info(self, method, url, data=None, params=None, response=None, test_passed=True):
        """打印测试信息"""
        print(f"\n{'='*60}")
        print("测试信息:")
        print(f"  方法: {method}")
        print(f"  URL: {url}")
        if params:
            print(f"  查询参数: {params}")
        if data:
            print(f"  请求数据: {data}")
        if response:
            print(f"  响应状态: {response.status_code}")
            print(f"  响应数据: {response.data}")
        print(f"  测试结果: {'通过' if test_passed else '失败'}")
        print(f"{'='*60}")

    def test_get_activities_list_success(self):
        """测试成功获取活动列表"""
        url = reverse('activities')
        params = {'weixin_id': self.member_weixin_id}
        response = self.client.get(url, params)

        test_passed = (
            response.status_code == status.HTTP_200_OK and
            response.data['weixin_id'] == self.member_weixin_id and
            response.data['count'] == 1 and
            len(response.data['data']) == 1 and
            response.data['data'][0]['activity_title'] == '测试活动'
        )

        self._log_test_info('GET', url, params=params, response=response, test_passed=test_passed)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['weixin_id'], self.member_weixin_id)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(len(response.data['data']), 1)
        self.assertEqual(response.data['data'][0]['activity_title'], '测试活动')

    def test_get_activities_list_missing_weixin_id(self):
        """测试缺少 weixin_id 参数"""
        url = reverse('activities')
        response = self.client.get(url)

        test_passed = (
            response.status_code == status.HTTP_400_BAD_REQUEST and
            'error' in response.data
        )

        self._log_test_info('GET', url, response=response, test_passed=test_passed)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_create_activity_success(self):
        """测试成功创建活动"""
        url = reverse('activities')
        data = {
            'creator_weixin_id': 'new_creator',
            'creator_weixin_name': '新创建者',
            'activity_title': '新活动',
            'activity_items': ['事项1', '事项2', '事项3'],
            'white_list': ['new_creator', 'friend_123']
        }
        response = self.client.post(url, data, format='json')

        test_passed = (
            response.status_code == status.HTTP_201_CREATED and
            response.data['activity_title'] == '新活动' and
            response.data['creator_weixin_id'] == 'new_creator' and
            len(response.data['activity_items']) == 3 and
            response.data['activity_items']['1']['name'] == '事项1'
        )

        self._log_test_info('POST', url, data=data, response=response, test_passed=test_passed)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['activity_title'], '新活动')
        self.assertEqual(response.data['creator_weixin_id'], 'new_creator')
        self.assertEqual(len(response.data['activity_items']), 3)
        self.assertEqual(response.data['activity_items']['1']['name'], '事项1')

    def test_create_activity_missing_required_fields(self):
        """测试创建活动时缺少必需字段"""
        url = reverse('activities')
        data = {
            'creator_weixin_id': 'new_creator',
            # 缺少其他必需字段
        }
        response = self.client.post(url, data, format='json')

        test_passed = (
            response.status_code == status.HTTP_400_BAD_REQUEST and
            'error' in response.data
        )

        self._log_test_info('POST', url, data=data, response=response, test_passed=test_passed)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_get_activity_detail_success(self):
        """测试成功获取活动详情"""
        url = reverse('activity', kwargs={'activity_id': self.activity.id})
        response = self.client.get(url)

        test_passed = (
            response.status_code == status.HTTP_200_OK and
            response.data['activity_title'] == '测试活动' and
            response.data['creator_weixin_id'] == self.creator_weixin_id
        )

        self._log_test_info('GET', url, response=response, test_passed=test_passed)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['activity_title'], '测试活动')
        self.assertEqual(response.data['creator_weixin_id'], self.creator_weixin_id)

    def test_get_nonexistent_activity(self):
        """测试获取不存在的活动"""
        url = reverse('activity', kwargs={'activity_id': 999})
        response = self.client.get(url)

        test_passed = response.status_code == status.HTTP_404_NOT_FOUND

        self._log_test_info('GET', url, response=response, test_passed=test_passed)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_activity_title_success(self):
        """测试成功更新活动标题"""
        url = reverse('activity', kwargs={'activity_id': self.activity.id})
        data = {
            'weixin_id': self.creator_weixin_id,
            'activity_title': '更新后的标题'
        }
        response = self.client.put(url, data, format='json')

        test_passed = (
            response.status_code == status.HTTP_200_OK and
            response.data['activity_title'] == '更新后的标题'
        )

        self._log_test_info('PUT', url, data=data, response=response, test_passed=test_passed)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['activity_title'], '更新后的标题')

        # 验证数据库已更新
        self.activity.refresh_from_db()
        self.assertEqual(self.activity.activity_title, '更新后的标题')

    def test_update_activity_title_unauthorized(self):
        """测试无权限更新活动标题"""
        url = reverse('activity', kwargs={'activity_id': self.activity.id})
        data = {
            'weixin_id': self.other_weixin_id,
            'activity_title': '更新后的标题'
        }
        response = self.client.put(url, data, format='json')

        test_passed = response.status_code == status.HTTP_403_FORBIDDEN

        self._log_test_info('PUT', url, data=data, response=response, test_passed=test_passed)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_activity_success(self):
        """测试成功删除活动"""
        url = reverse('activity', kwargs={'activity_id': self.activity.id})
        data = {
            'weixin_id': self.creator_weixin_id
        }
        response = self.client.delete(url, data, format='json')

        test_passed = (
            response.status_code == status.HTTP_200_OK and
            not Activities.objects.filter(id=self.activity.id).exists()
        )

        self._log_test_info('DELETE', url, data=data, response=response, test_passed=test_passed)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(Activities.objects.filter(id=self.activity.id).exists())

    def test_delete_activity_unauthorized(self):
        """测试无权限删除活动"""
        url = reverse('activity', kwargs={'activity_id': self.activity.id})
        data = {
            'weixin_id': self.other_weixin_id
        }
        response = self.client.delete(url, data, format='json')

        test_passed = (
            response.status_code == status.HTTP_403_FORBIDDEN and
            Activities.objects.filter(id=self.activity.id).exists()
        )

        self._log_test_info('DELETE', url, data=data, response=response, test_passed=test_passed)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Activities.objects.filter(id=self.activity.id).exists())

    def test_update_white_list_success(self):
        """测试成功更新白名单"""
        url = reverse('activity_white_list', kwargs={'activity_id': self.activity.id})
        data = {
            'weixin_id': self.creator_weixin_id,
            'white_list': [self.creator_weixin_id, 'new_member_1', 'new_member_2']
        }
        response = self.client.put(url, data, format='json')

        test_passed = (
            response.status_code == status.HTTP_200_OK and
            len(response.data['white_list']) == 3
        )

        self._log_test_info('PUT', url, data=data, response=response, test_passed=test_passed)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['white_list']), 3)

        # 验证数据库已更新
        self.activity.refresh_from_db()
        self.assertEqual(len(self.activity.white_list), 3)

    def test_update_white_list_unauthorized(self):
        """测试无权限更新白名单"""
        url = reverse('activity_white_list', kwargs={'activity_id': self.activity.id})
        data = {
            'weixin_id': self.other_weixin_id,
            'white_list': ['new_member']
        }
        response = self.client.put(url, data, format='json')

        test_passed = response.status_code == status.HTTP_403_FORBIDDEN

        self._log_test_info('PUT', url, data=data, response=response, test_passed=test_passed)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_add_activity_item_success(self):
        """测试成功添加活动事项"""
        url = reverse('activity_items', kwargs={'activity_id': self.activity.id})
        data = {
            'weixin_id': self.member_weixin_id,
            'activity_item_name': '新事项'
        }
        response = self.client.post(url, data, format='json')

        test_passed = (
            response.status_code == status.HTTP_200_OK and
            len(response.data['activity_items']) == 3 and
            response.data['activity_items']['3']['name'] == '新事项' and
            response.data['activity_items']['3']['status'] == '' and
            response.data['activity_items']['3']['operator'] == ''
        )

        self._log_test_info('POST', url, data=data, response=response, test_passed=test_passed)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['activity_items']), 3)
        self.assertEqual(response.data['activity_items']['3']['name'], '新事项')
        self.assertEqual(response.data['activity_items']['3']['status'], '')
        self.assertEqual(response.data['activity_items']['3']['operator'], '')

    def test_add_activity_item_unauthorized(self):
        """测试无权限添加活动事项"""
        url = reverse('activity_items', kwargs={'activity_id': self.activity.id})
        data = {
            'weixin_id': self.other_weixin_id,
            'activity_item_name': '新事项'
        }
        response = self.client.post(url, data, format='json')

        test_passed = response.status_code == status.HTTP_403_FORBIDDEN

        self._log_test_info('POST', url, data=data, response=response, test_passed=test_passed)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_activity_item_success(self):
        """测试成功更新活动事项状态"""
        url = reverse('activity_item', kwargs={
            'activity_id': self.activity.id,
            'item_id': '1'
        })
        data = {
            'weixin_id': self.member_weixin_id,
            'activity_item_status': 'completed'
        }
        response = self.client.put(url, data, format='json')

        test_passed = (
            response.status_code == status.HTTP_200_OK and
            response.data['activity_items']['1']['status'] == 'completed' and
            response.data['activity_items']['1']['operator'] == self.member_weixin_id
        )

        self._log_test_info('PUT', url, data=data, response=response, test_passed=test_passed)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['activity_items']['1']['status'], 'completed')
        self.assertEqual(response.data['activity_items']['1']['operator'], self.member_weixin_id)

    def test_update_activity_item_reset_status(self):
        """测试重置活动事项状态"""
        # 先设置状态
        self.activity.activity_items['1']['status'] = 'completed'
        self.activity.activity_items['1']['operator'] = self.member_weixin_id
        self.activity.save()

        url = reverse('activity_item', kwargs={
            'activity_id': self.activity.id,
            'item_id': '1'
        })
        data = {
            'weixin_id': self.member_weixin_id,
            'activity_item_status': ''
        }
        response = self.client.put(url, data, format='json')

        test_passed = (
            response.status_code == status.HTTP_200_OK and
            response.data['activity_items']['1']['status'] == '' and
            response.data['activity_items']['1']['operator'] == ''
        )

        self._log_test_info('PUT', url, data=data, response=response, test_passed=test_passed)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['activity_items']['1']['status'], '')
        self.assertEqual(response.data['activity_items']['1']['operator'], '')

    def test_update_activity_item_locked(self):
        """测试更新被其他人锁定的活动事项"""
        # 设置事项已被其他人操作
        self.activity.activity_items['1']['status'] = 'completed'
        self.activity.activity_items['1']['operator'] = 'other_user'
        self.activity.save()

        url = reverse('activity_item', kwargs={
            'activity_id': self.activity.id,
            'item_id': '1'
        })
        data = {
            'weixin_id': self.member_weixin_id,
            'activity_item_status': 'completed'
        }
        response = self.client.put(url, data, format='json')

        test_passed = (
            response.status_code == status.HTTP_400_BAD_REQUEST and
            'error' in response.data
        )

        self._log_test_info('PUT', url, data=data, response=response, test_passed=test_passed)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_delete_activity_item_success(self):
        """测试成功删除活动事项"""
        url = reverse('activity_item', kwargs={
            'activity_id': self.activity.id,
            'item_id': '1'
        })
        data = {
            'weixin_id': self.member_weixin_id
        }
        response = self.client.delete(url, data, format='json')

        test_passed = (
            response.status_code == status.HTTP_200_OK and
            '1' not in response.data['activity_items'] and
            '2' in response.data['activity_items']
        )

        self._log_test_info('DELETE', url, data=data, response=response, test_passed=test_passed)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn('1', response.data['activity_items'])
        self.assertIn('2', response.data['activity_items'])

    def test_delete_nonexistent_activity_item(self):
        """测试删除不存在的活动事项"""
        url = reverse('activity_item', kwargs={
            'activity_id': self.activity.id,
            'item_id': '999'
        })
        data = {
            'weixin_id': self.member_weixin_id
        }
        response = self.client.delete(url, data, format='json')

        test_passed = response.status_code == status.HTTP_404_NOT_FOUND

        self._log_test_info('DELETE', url, data=data, response=response, test_passed=test_passed)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
