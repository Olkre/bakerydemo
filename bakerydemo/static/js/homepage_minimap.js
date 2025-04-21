document.addEventListener("DOMContentLoaded", function () {
  const hash = window.location.hash;
  console.log("hash is", hash);

  if (hash) {
      let tries = 0;
      const maxTries = 30;

      const scrollToElement = () => {
          const el = document.querySelector(hash);
          console.log(`[Try ${tries}] Element:`, el);

          if (el) {
              const rect = el.getBoundingClientRect();
              const isVisible = rect.height > 0 && rect.width > 0;

              console.log(`[Try ${tries}] Visible?`, isVisible, "Collapsed?", el.closest('[data-panel].collapsed'));

              if (!isVisible) {
                  // Try expanding parent panels
                  const collapsedParent = el.closest('[data-panel].collapsed');
                  if (collapsedParent) {
                      const toggleBtn = collapsedParent.querySelector('[aria-expanded="false"]');
                      console.log("Clicking toggle to expand:", toggleBtn);
                      if (toggleBtn) toggleBtn.click();
                  }
              }

              setTimeout(() => {
                  console.log("Scrolling into view...");
                  el.scrollIntoView({ behavior: "smooth", block: "start" });
              }, 200); // delay slightly to allow expand animation
          }

          if (++tries < maxTries) {
              setTimeout(scrollToElement, 300);
          }
      };

      scrollToElement();
  }

  console.log("initialized scroll attempt");
});