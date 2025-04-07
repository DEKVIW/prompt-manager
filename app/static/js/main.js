document.addEventListener("DOMContentLoaded", function () {
  // 初始化工具提示
  var tooltipTriggerList = [].slice.call(
    document.querySelectorAll('[data-bs-toggle="tooltip"]')
  );
  var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });

  // 复制按钮功能
  const copyButtons = document.querySelectorAll(".btn-copy");
  if (copyButtons.length > 0) {
    copyButtons.forEach((button) => {
      button.addEventListener("click", function () {
        const textToCopy = document.getElementById(
          this.getAttribute("data-copy-target")
        ).textContent;

        // 使用剪贴板API复制文本
        navigator.clipboard
          .writeText(textToCopy)
          .then(() => {
            // 复制成功，更改按钮文本
            const originalText = this.innerHTML;
            this.innerHTML = '<i class="bi bi-check-lg"></i> 已复制';
            this.classList.remove("btn-outline-primary");
            this.classList.add("btn-success");

            // 2秒后恢复按钮原始状态
            setTimeout(() => {
              this.innerHTML = originalText;
              this.classList.remove("btn-success");
              this.classList.add("btn-outline-primary");
            }, 2000);
          })
          .catch((err) => {
            console.error("复制失败:", err);
            alert("复制失败，请手动复制");
          });
      });
    });
  }

  // 提示词分享功能
  const shareButtons = document.querySelectorAll(".btn-share");
  if (shareButtons.length > 0) {
    shareButtons.forEach((button) => {
      button.addEventListener("click", function (e) {
        e.preventDefault();
        const promptId = this.getAttribute("data-prompt-id");

        // 发送AJAX请求
        fetch(`/prompts/${promptId}/share`)
          .then((response) => response.json())
          .then((data) => {
            if (data.success) {
              // 使用Web Share API分享（如果可用）
              if (navigator.share) {
                navigator
                  .share({
                    title: document.title,
                    url: data.url,
                  })
                  .catch((err) => {
                    // 如果Web Share API不可用，直接复制链接
                    copyToClipboard(data.url);
                  });
              } else {
                // 复制链接到剪贴板
                copyToClipboard(data.url);
              }
            }
          })
          .catch((error) => {
            console.error("分享错误:", error);
          });
      });
    });
  }

  // 辅助函数：复制到剪贴板
  function copyToClipboard(text) {
    navigator.clipboard
      .writeText(text)
      .then(() => {
        // 显示复制成功提示
        const alertDiv = document.createElement("div");
        alertDiv.className = "alert alert-success alert-dismissible fade show";
        alertDiv.innerHTML = `
                链接已复制到剪贴板！
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            `;
        document.querySelector(".container").prepend(alertDiv);

        // 2秒后自动关闭提示
        setTimeout(() => {
          const bsAlert = new bootstrap.Alert(alertDiv);
          bsAlert.close();
        }, 2000);
      })
      .catch((err) => {
        console.error("复制失败:", err);
        alert("复制链接失败，请手动复制");
      });
  }

  // 删除提示词确认
  const deleteButtons = document.querySelectorAll(".btn-delete-prompt");
  if (deleteButtons.length > 0) {
    deleteButtons.forEach((button) => {
      button.addEventListener("click", function (e) {
        if (!confirm("确定要删除这个提示词吗？此操作不可撤销。")) {
          e.preventDefault();
        }
      });
    });
  }

  // 标签筛选功能
  const tagFilters = document.querySelectorAll(".tag-filter");
  if (tagFilters.length > 0) {
    tagFilters.forEach((tag) => {
      tag.addEventListener("click", function (e) {
        e.preventDefault();
        const tagName = this.getAttribute("data-tag");
        window.location.href = `/search?tag=${encodeURIComponent(tagName)}`;
      });
    });
  }
});
