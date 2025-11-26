/**
 * 提示词管理平台 - 主JavaScript文件
 */

// 等待文档加载完成
document.addEventListener("DOMContentLoaded", function () {
  // 初始化所有功能
  initTooltips();
  initAnimations();
  initCopyButtons();
  initTagEffects();
  initFlashMessages();
  initFormValidation();
  initImagePreview();
  initScrollNavbar();
  initCardAnimations();
  initPageTransitions();
  initStaggeredItems();

  // 删除此处的回到顶部按钮代码，避免冲突
  console.log("main.js初始化完成，回到顶部按钮已由HTML内联脚本处理");
});

/**
 * 初始化 Bootstrap 工具提示
 */
function initTooltips() {
  const tooltipTriggerList = document.querySelectorAll(
    '[data-bs-toggle="tooltip"]'
  );
  if (tooltipTriggerList.length > 0 && typeof bootstrap !== "undefined") {
    tooltipTriggerList.forEach(function (tooltipTriggerEl) {
      new bootstrap.Tooltip(tooltipTriggerEl);
    });
    console.log("工具提示已初始化");
  }
}

/**
 * 初始化动画效果
 */
function initAnimations() {
  const mainContent = document.querySelector("main");
  if (mainContent) {
    mainContent.classList.add("fade-in");
  }

  const headings = document.querySelectorAll("h1, h2, h3");
  headings.forEach(function (heading) {
    heading.classList.add("fadeIn");
  });
}

/**
 * 初始化复制按钮功能
 */
function initCopyButtons() {
  const copyButtons = document.querySelectorAll("[data-copy-target]");

  copyButtons.forEach(function (button) {
    button.addEventListener("click", function () {
      const targetId = button.getAttribute("data-copy-target");
      const targetElement = document.getElementById(targetId);

      if (targetElement) {
        if (
          targetElement.tagName === "INPUT" ||
          targetElement.tagName === "TEXTAREA"
        ) {
          copyToClipboard(targetElement.value, button);
        } else {
          copyToClipboard(targetElement.textContent, button);
        }
      }
    });
  });

  const copyTextButtons = document.querySelectorAll("[data-copy-text]");

  copyTextButtons.forEach(function (button) {
    button.addEventListener("click", function () {
      const text = button.getAttribute("data-copy-text");
      copyToClipboard(text, button);
    });
  });
}

/**
 * 复制内容到剪贴板
 */
function copyToClipboard(text, button) {
  // 保存原始按钮文本，用于恢复
  const originalText = button.innerHTML;

  // 检查是否支持现代Clipboard API
  if (navigator.clipboard && window.isSecureContext) {
    // 使用现代Clipboard API
    navigator.clipboard
      .writeText(text)
      .then(() => {
        // 复制成功
        button.innerHTML = '<i class="bi bi-check"></i> 已复制';

        // 显示成功消息（可选）
        if (window.innerWidth < 768) {
          // 移动端显示toast提示
          showToast("复制成功", "success");
        }

        // 2秒后恢复按钮原样
        setTimeout(function () {
          button.innerHTML = originalText;
        }, 2000);
      })
      .catch((err) => {
        console.error("复制失败:", err);
        button.innerHTML =
          '<i class="bi bi-exclamation-triangle"></i> 复制失败';

        // 添加备用复制方法
        fallbackCopyToClipboard(text, button, originalText);

        setTimeout(function () {
          button.innerHTML = originalText;
        }, 2000);
      });
  } else {
    // 对于不支持Clipboard API的浏览器，使用备用方法
    fallbackCopyToClipboard(text, button, originalText);
  }
}

/**
 * 备用的复制方法，使用传统技术
 */
function fallbackCopyToClipboard(text, button, originalText) {
  try {
    // 创建临时textarea
    const textarea = document.createElement("textarea");
    textarea.value = text;

    // 确保textarea在移动设备上可见（在视口内但不可见）
    textarea.style.position = "fixed";
    textarea.style.left = "0";
    textarea.style.top = "0";
    textarea.style.opacity = "0";
    textarea.style.width = "100%";
    textarea.style.height = "100%";

    document.body.appendChild(textarea);

    // 特殊处理iOS设备
    if (/iPhone|iPad|iPod/.test(navigator.userAgent)) {
      const range = document.createRange();
      range.selectNodeContents(textarea);
      const selection = window.getSelection();
      selection.removeAllRanges();
      selection.addRange(range);
      textarea.setSelectionRange(0, 999999);
    } else {
      textarea.select();
    }

    const successful = document.execCommand("copy");
    document.body.removeChild(textarea);

    if (successful) {
      button.innerHTML = '<i class="bi bi-check"></i> 已复制';

      // 移动端显示额外提示
      if (window.innerWidth < 768) {
        showToast("复制成功", "success");
      }
    } else {
      console.error("复制失败");
      button.innerHTML =
        '<i class="bi bi-exclamation-triangle"></i> 失败，请手动复制';

      // 移动端显示提示
      if (window.innerWidth < 768) {
        showToast("请手动长按并复制内容", "warning");
      }
    }
  } catch (err) {
    console.error("复制过程中出错:", err);
    button.innerHTML =
      '<i class="bi bi-exclamation-triangle"></i> 失败，请手动复制';
  }

  // 2秒后恢复按钮原样
  setTimeout(function () {
    button.innerHTML = originalText;
  }, 2000);
}

/**
 * 显示Toast提示消息（不占据页面布局）
 * @param {string} message - 消息内容
 * @param {string} type - 消息类型：success, danger, warning, info
 * @param {number} duration - 显示时长（毫秒），默认3000，0表示不自动关闭
 */
function showToastNotification(message, type = "success", duration = 3000) {
  const container = document.getElementById("toast-container");
  if (!container) {
    console.error("Toast container not found");
    return;
  }

  // 创建 Toast 元素
  const toast = document.createElement("div");
  toast.className = `toast-notification toast-${type}`;
  toast.setAttribute("role", "alert");
  toast.setAttribute("aria-live", "assertive");

  // 根据类型设置图标
  let icon = "bi-info-circle";
  if (type === "success") {
    icon = "bi-check-circle";
  } else if (type === "danger") {
    icon = "bi-exclamation-circle";
  } else if (type === "warning") {
    icon = "bi-exclamation-triangle";
  }

  // 设置内容
  toast.innerHTML = `
    <i class="bi ${icon} toast-icon"></i>
    <div class="toast-message">${escapeHtml(message)}</div>
    <button type="button" class="toast-close" aria-label="关闭">
      <i class="bi bi-x"></i>
    </button>
  `;

  // 添加到容器
  container.appendChild(toast);

  // 关闭按钮事件
  const closeBtn = toast.querySelector(".toast-close");
  closeBtn.addEventListener("click", () => {
    removeToast(toast);
  });

  // 自动关闭
  if (duration > 0) {
    setTimeout(() => {
      removeToast(toast);
    }, duration);
  }

  return toast;
}

/**
 * 移除 Toast 通知
 */
function removeToast(toast) {
  if (!toast || !toast.parentNode) return;

  toast.classList.add("toast-fade-out");
  setTimeout(() => {
    if (toast.parentNode) {
      toast.remove();
    }
  }, 300);
}

/**
 * HTML 转义函数
 */
function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

/**
 * 显示Toast提示消息（兼容旧版本）
 * @deprecated 使用 showToastNotification 代替
 */
function showToast(message, type = "success") {
  showToastNotification(message, type, 2000);
}

/**
 * 初始化标签点击动画
 */
function initTagEffects() {
  const tags = document.querySelectorAll(".tag, .tag-pill");

  tags.forEach(function (tag) {
    tag.addEventListener("mouseenter", function () {
      this.style.transform = "translateY(-5px) scale(1.05)";
    });

    tag.addEventListener("mouseleave", function () {
      this.style.transform = "";
    });
  });
}

/**
 * 初始化闪烁消息自动消失
 */
function initFlashMessages() {
  const flashMessages = document.querySelectorAll(".alert");

  flashMessages.forEach(function (message) {
    message.classList.add("fade-in");

    const closeButton = message.querySelector(".btn-close");
    if (closeButton) {
      closeButton.addEventListener("click", function () {
        message.classList.add("fade-out");

        setTimeout(function () {
          message.remove();
        }, 500);
      });
    }

    if (!message.classList.contains("alert-danger")) {
      setTimeout(function () {
        message.classList.add("fade-out");

        setTimeout(function () {
          if (message.parentNode) {
            message.remove();
          }
        }, 500);
      }, 5000);
    }
  });
}

/**
 * 表单验证
 */
function initFormValidation() {
  const forms = document.querySelectorAll(".needs-validation");

  forms.forEach(function (form) {
    form.addEventListener(
      "submit",
      function (event) {
        if (!form.checkValidity()) {
          event.preventDefault();
          event.stopPropagation();
        }

        form.classList.add("was-validated");
      },
      false
    );
  });
}

/**
 * 图片预览
 */
function initImagePreview() {
  const fileInputs = document.querySelectorAll(
    'input[type="file"][data-preview-target]'
  );

  fileInputs.forEach(function (input) {
    input.addEventListener("change", function () {
      const targetId = input.getAttribute("data-preview-target");
      const previewElement = document.getElementById(targetId);

      if (previewElement && input.files && input.files[0]) {
        const reader = new FileReader();

        reader.onload = function (e) {
          if (previewElement.tagName === "IMG") {
            previewElement.src = e.target.result;
            previewElement.style.display = "block";
          } else {
            previewElement.style.backgroundImage = `url(${e.target.result})`;
          }

          previewElement.classList.add("preview-loaded");
        };

        reader.readAsDataURL(input.files[0]);
      }
    });
  });
}

/**
 * 初始化滚动导航栏
 */
function initScrollNavbar() {
  let lastScrollTop = 0;
  const navbar = document.querySelector(".navbar");
  const scrollThreshold = 100;

  if (navbar) {
    navbar.classList.add("navbar-visible");

    window.addEventListener(
      "scroll",
      function () {
        const currentScrollTop =
          window.pageYOffset || document.documentElement.scrollTop;

        if (currentScrollTop > scrollThreshold) {
          if (currentScrollTop > lastScrollTop) {
            navbar.classList.remove("navbar-visible");
            navbar.classList.add("navbar-hidden");
          } else {
            navbar.classList.remove("navbar-hidden");
            navbar.classList.add("navbar-visible");
          }
        } else {
          navbar.classList.remove("navbar-hidden");
          navbar.classList.add("navbar-visible");
        }

        setTimeout(function () {
          lastScrollTop = currentScrollTop;
        }, 100);
      },
      { passive: true }
    );
  }
}

/**
 * 页面过渡动画
 */
function initPageTransitions() {
  document.querySelectorAll("a").forEach((link) => {
    if (
      link.hostname === window.location.hostname &&
      !link.hasAttribute("data-no-transition") &&
      !link.getAttribute("href").startsWith("#") &&
      !link.getAttribute("href").includes("javascript:")
    ) {
      link.addEventListener("click", function (e) {
        e.preventDefault();

        const targetUrl = this.getAttribute("href");

        document.body.classList.add("page-exit");

        setTimeout(() => {
          window.location.href = targetUrl;
        }, 300);
      });
    }
  });

  window.addEventListener("pageshow", function () {
    document.body.classList.add("page-enter");
    document.body.classList.remove("page-exit");
  });
}

/**
 * 为卡片添加进场动画
 */
function initCardAnimations() {
  const cards = document.querySelectorAll(".card");

  if (cards.length > 0) {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("card-visible");
            observer.unobserve(entry.target);
          }
        });
      },
      {
        threshold: 0.1,
      }
    );

    cards.forEach((card, index) => {
      card.classList.add("card-animate");
      card.style.animationDelay = `${index * 0.05}s`;
      observer.observe(card);
    });
  }
}

/**
 * 执行错开动画的元素
 */
function initStaggeredItems() {
  const staggerContainers = document.querySelectorAll(".stagger-container");

  staggerContainers.forEach((container) => {
    const items = container.querySelectorAll(".stagger-item");

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          items.forEach((item, index) => {
            setTimeout(() => {
              item.classList.add("stagger-visible");
            }, index * 100);
          });
          observer.unobserve(container);
        }
      },
      {
        threshold: 0.1,
      }
    );

    observer.observe(container);
  });
}
