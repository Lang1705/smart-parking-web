// 1. Update Hari, Tanggal, Tahun & Jam Digital Real-Time
function updateClock() {
    const dateEl = document.getElementById('liveDate');
    const clockEl = document.getElementById('liveClock');
    if (!dateEl && !clockEl) return;

    const now = new Date();
    const dateOptions = {
        weekday: 'long',
        day: 'numeric',
        month: 'long',
        year: 'numeric'
    };
    const timeOptions = {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false
    };

    if (dateEl) {
        dateEl.innerText = '📅 ' + now.toLocaleDateString('id-ID', dateOptions);
    }
    if (clockEl) {
        clockEl.innerText = '🕒 ' + now.toLocaleTimeString('id-ID', timeOptions) + ' WIB';
    }
}
setInterval(updateClock, 1000);
updateClock();
