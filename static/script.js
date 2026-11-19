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

// Ambil konteks status member dari atribut HTML
const appCtx = document.getElementById('appContext');
const isMember = appCtx ? appCtx.dataset.isMember === 'true' : false;
const memberPlatTersimpan = appCtx ? appCtx.dataset.userPlat : '';

// 2. Buka Modal Pop-Up Saat Klik Kotak Tempat Parkir
function bukaModalParkir(kodeSlot) {
    const modal = document.getElementById('modalParkir');
    const slotInput = document.getElementById('slot_pilihan');
    const modalTitle = document.getElementById('modalTitle');
    const paySlotLabel = document.getElementById('paySlotLabel');

    if (slotInput) slotInput.value = kodeSlot;
    if (modalTitle) modalTitle.innerText = 'Booking Slot ' + kodeSlot;
    if (paySlotLabel) paySlotLabel.innerText = kodeSlot;

    // Reset ke Langkah 1 (Data Kendaraan)
    kembaliKeData();

    if (isMember) {
        pilihModePlat('lama');
    } else {
        const platInput = document.getElementById('plat_nomor');
        if (platInput) platInput.value = '';
    }

    updateTarifModal();

    if (modal) modal.classList.add('active');
}

function tutupModalParkir() {
    const modal = document.getElementById('modalParkir');
    if (modal) modal.classList.remove('active');
}

function tutupModalLuar(event) {
    if (event.target.id === 'modalParkir') {
        tutupModalParkir();
    }
}

// 3. Khusus Member: Pilih Pakai Plat Terdaftar atau Buat Plat Baru
function pilihModePlat(mode) {
    const btnLama = document.getElementById('btnPlatLama');
    const btnBaru = document.getElementById('btnPlatBaru');
    const platInput = document.getElementById('plat_nomor');
    if (!platInput) return;

    if (mode === 'lama') {
        if (btnLama) btnLama.classList.add('active');
        if (btnBaru) btnBaru.classList.remove('active');
        platInput.value = memberPlatTersimpan;
        platInput.readOnly = true;
    } else {
        if (btnBaru) btnBaru.classList.add('active');
        if (btnLama) btnLama.classList.remove('active');
        platInput.value = '';
        platInput.readOnly = false;
        platInput.placeholder = 'Masukkan nomor plat baru...';
        platInput.focus();
    }
}

// 4. Hitung Tarif Otomatis (Diskon 10% untuk Member)
function updateTarifModal() {
    const durasiEl = document.getElementById('durasi');
    const normalEl = document.getElementById('previewTarifNormal');
    const diskonEl = document.getElementById('previewDiskon');
    const hargaEl = document.getElementById('previewHarga');
    const payTotalBig = document.getElementById('payTotalBig');
    if (!durasiEl || !hargaEl) return;

    const jam = parseInt(durasiEl.value, 10) || 1;
    const tarifNormal = jam <= 1 ? 5000 : 5000 + (jam - 1) * 3000;
    const diskon = isMember ? Math.round(tarifNormal * 0.10) : 0;
    const totalAkhir = tarif
