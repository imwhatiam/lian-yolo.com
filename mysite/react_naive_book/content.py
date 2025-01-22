code_content_1 = """
<div class='wrapper'>
  <button class='like-btn'>
    <span class='like-text'>点赞</span>
    <span>👍</span>
  </button>
</div>

<script>
const button = document.querySelector('.like-btn')
const buttonText = button.querySelector('.like-text')
let isLiked = false
button.addEventListener('click', () => {
  isLiked = !isLiked
  if (isLiked) {
    buttonText.innerHTML = '取消'
  } else {
    buttonText.innerHTML = '点赞'
  }
}, false)
</script>
"""

markdown_content_1 = """
在 JavaScript 的 `addEventListener` 方法中，`false` 作为第三个参数，表示事件监听器的 **选项**，具体来说，它定义了事件监听器的行为方式。这个位置可以是布尔值，也可以是一个选项对象。

### 参数位置说明：
```javascript
target.addEventListener(type, listener, options);
```

1. **`type`**: 字符串，表示监听的事件类型（如 `"click"`）。
2. **`listener`**: 事件处理函数，当指定事件触发时调用。
3. **`options`**（或布尔值 `capture`）：
   - 如果是布尔值，`true` 表示启用事件捕获阶段，`false` 表示启用事件冒泡阶段（默认值）。
   - 如果是对象，则可以指定多个选项。

---

### `false` 的含义：
`false` 在这里表示 **事件冒泡阶段** 被触发时，执行这个监听器。

- **事件冒泡（Event Bubbling）**:
  事件从目标元素开始，向上冒泡到祖先元素。例如，`button` 内的 `span` 被点击，事件会向上传递到 `button`、`div` 等祖先节点。

- **事件捕获（Event Capturing）**:
  事件从祖先元素开始，向下传递到目标元素。

默认情况下，`addEventListener` 使用事件冒泡阶段，因此通常设置 `false` 或忽略该参数。

---

### 使用选项对象的替代方式：
从现代浏览器开始，可以使用一个选项对象替代布尔值，来明确指定更多的监听行为：

```javascript
button.addEventListener('click', () => {
  isLiked = !isLiked;
  buttonText.innerHTML = isLiked ? '取消' : '点赞';
}, { capture: false });
```

### 可用的选项：
1. **`capture`**: 布尔值，`true` 表示在捕获阶段调用监听器，`false` 表示在冒泡阶段调用（默认）。
2. **`once`**: 布尔值，`true` 表示事件监听器只会触发一次，触发后自动移除。
3. **`passive`**: 布尔值，`true` 表示监听器不会调用 `preventDefault()`，以提升性能（适用于滚动事件）。

例如：
```javascript
button.addEventListener('click', () => {
  console.log('Clicked!');
}, { once: true });
```

在此例中，按钮的点击事件监听器只触发一次，随后自动移除。

---

### 总结：
在你提供的代码中：
- `false` 表示事件监听器在 **冒泡阶段** 执行。
- 若需更复杂的控制，可以用选项对象代替简单的布尔值。
"""

CODE_CONTENT_DICT = {
    1: code_content_1,
}

MARKDOWN_CONTENT_DICT = {
    1: markdown_content_1,
}


def get_code_content(lesson_number):
    return CODE_CONTENT_DICT[lesson_number]


def get_markdown_content(lesson_number):
    return MARKDOWN_CONTENT_DICT[lesson_number]
