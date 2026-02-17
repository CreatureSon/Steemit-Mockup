// timer.js
document.addEventListener("DOMContentLoaded", () => {
    const joinedAt = document.body.dataset.joinedAt;
    console.log("Timer started at:", joinedAt);
    if (!joinedAt) return;

    //const limitMs = 10 * 60 * 1000;
    const limitMs = 1 * 60 * 1000;
    const start = new Date(joinedAt);
    const remaining = limitMs - (Date.now() - start.getTime());

    console.log("Timer started at:", joinedAt);
    if (remaining > 0) {
        setTimeout(() => {
            window.location.href = "/participants/end/";
        }, remaining);
    } else {
        window.location.href = "/participants/end/";
    }
});