// Jam & Tanggal Real-Time (WIB)
function updateDateTimeLive() {
    const dateEl = document.getElementById('liveDate');
    const clockEl = document.getElementById('liveClock');
    if (!dateEl || !clockEl) return;

    const now = new Date();
    const hariList = ['Minggu', 'Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu'];
    const bulanList = [
        'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
        'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'
    ];

    const hari = hariList[now.getDay()];
    const tanggal = now.getDate();
    const bulan = bulanList[now.getMonth()];
    const tahun = now.getFullYear();

    const jam = String(now.getHours()).padStart(2, '0');
    const menit = String(now.getMinutes()).padStart(2, '0');
    const detik = String(now.getSeconds()).padStart(2, '0');

    dateEl.textContent = `📅 ${hari}, ${tanggal} ${bulan} ${tahun}`;
    clockEl.textContent = `🕒 ${jam}:${menit}:${detik} WIB`;
}

setInterval(updateDateTimeLive, 1000);
updateDateTimeLive();

// Format Rupiah
function formatRupiah(angka) {
    return 'Rp' + angka.toString().replace(/\B(?=(\d{3})+(?!\d))/g, '.');
}

// Hitung Tarif Dinamis di Modal
function updateTarifModal() {
    const durasiEl = document.getElementById('durasi');
    if (!durasiEl) return;

    const durasi = parseInt(durasiEl.value, 10) || 1;
    const appCtx = document.getElementById('appContext');
    const isMember = appCtx && appCtx.dataset.isMember === 'true';

    const tarifNormal = durasi <= 1 ? 5000 : 5000 + (durasi - 1) * 3000;
    const diskon = isMember ? Math.floor(tarifNormal * 0.10) : 0;
    const totalBayar = tarifNormal - diskon;

    document.getElementById('previewTarifNormal').textContent = formatRupiah(tarifNormal);
    document.getElementById('previewDiskon').textContent = '- ' + formatRupiah(diskon);
    document.getElementById('previewHarga').textContent = formatRupiah(totalBayar);
    document.getElementById('payTotalBig').textContent = formatRupiah(totalBayar);
}

// Buka Modal saat Slot Hijau Diklik
function bukaModalParkir(kodeSlot) {
    const modal = document.getElementById('modalParkir');
    if (!modal) return;

    document.getElementById('slot_pilihan').value = kodeSlot;
    document.getElementById('modalTitle').textContent = `Booking Slot ${kodeSlot}`;
    document.getElementById('paySlotLabel').textContent = kodeSlot;

    kembaliKeData();
    updateTarifModal();
    modal.classList.add('active');
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

// Pilihan Plat Lama vs Plat Baru untuk Member
function pilihModePlat(mode) {
    const appCtx = document.getElementById('appContext');
    const platInput = document.getElementById('plat_nomor');
    const btnLama = document.getElementById('btnPlatLama');
    const btnBaru = document.getElementById('btnPlatBaru');
    if (!platInput || !appCtx) return;

    if (mode === 'lama') {
        platInput.value = appCtx.dataset.userPlat || '';
        platInput.readOnly = true;
        btnLama.classList.add('active');
        btnBaru.classList.remove('active');
    } else {
        platInput.value = '';
        platInput.readOnly = false;
        platInput.placeholder = 'Ketik plat kendaraan baru...';
        platInput.focus();
        btnBaru.classList.add('active');
        btnLama.classList.remove('active');
    }
}

// Navigasi Langkah 1 -> Langkah 2 (Pembayaran)
function lanjutKePembayaran() {
    const nama = document.getElementById('nama_pengendara').value.trim();
    const hp = document.getElementById('no_hp_booking').value.trim();
    const plat = document.getElementById('plat_nomor').value.trim();

    if (!nama || !hp || !plat) {
        alert('Mohon lengkapi Nama, Nomor HP, dan Plat Kendaraan terlebih dahulu!');
        return;
    }

    updateTarifModal();
    document.getElementById('stepData').style.display = 'none';
    document.getElementById('stepPayment').style.display = 'block';
    document.getElementById('modalStepTag').textContent = 'LANGKAH 2 OF 2 • PEMBAYARAN';
}

function kembaliKeData() {
    document.getElementById('stepData').style.display = 'block';
    document.getElementById('stepPayment').style.display = 'none';
    document.getElementById('modalStepTag').textContent = 'LANGKAH 1 OF 2 • DATA KENDARAAN';
}

// Pilih Metode Bayar QRIS vs Kasir
function pilihMetodeBayar(metode) {
    document.getElementById('metode_bayar').value = metode;
    const cardQris = document.getElementById('cardQris');
    const cardKasir = document.getElementById('cardKasir');
    const qrisBox = document.getElementById('qrisBox');
    const kasirBox = document.getElementById('kasirBox');

    if (metode === 'QRIS') {
        cardQris.classList.add('active');
        cardKasir.classList.remove('active');
        qrisBox.style.display = 'block';
        kasirBox.style.display = 'none';
    } else {
        cardKasir.classList.add('active');
        cardQris.classList.remove('active');
        kasirBox.style.display = 'block';
        qrisBox.style.display = 'none';
    }
}
