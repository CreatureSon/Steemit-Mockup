// timer.js
document.addEventListener("DOMContentLoaded", () => {
    const joinedAt = document.body.dataset.joinedAt;
    console.log("Timer started at:", joinedAt);
    if (!joinedAt) return;

    const limitMs = 10 * 60 * 1000;
    const start = new Date(joinedAt);

    const timerEl = document.getElementById("session-timer");
    const displayEl = document.getElementById("timer-display");

    function getRemaining() {
        return limitMs - (Date.now() - start.getTime());
    }

    function formatTime(ms) {
        const totalSeconds = Math.max(0, Math.floor(ms / 1000));
        const minutes = Math.floor(totalSeconds / 60);
        const seconds = totalSeconds % 60;
        return `${minutes}:${String(seconds).padStart(2, "0")}`;
    }

    function updateDisplay(remaining) {
        if (!displayEl) return;
        displayEl.textContent = formatTime(remaining);

        if (!timerEl) return;
        timerEl.classList.remove("timer-warning", "timer-danger");
        if (remaining <= 60 * 1000) {
            timerEl.classList.add("timer-danger");
        } else if (remaining <= 2 * 60 * 1000) {
            timerEl.classList.add("timer-warning");
        }
    }

    const remaining = getRemaining();

    if (remaining <= 0) {
        window.location.href = "/participants/end/";
        return;
    }

    // Set initial display immediately
    updateDisplay(remaining);

    // Tick every second
    const interval = setInterval(() => {
        const remaining = getRemaining();
        updateDisplay(remaining);

        if (remaining <= 0) {
            clearInterval(interval);
            window.location.href = "/participants/end/";
        }
    }, 1000);
});
