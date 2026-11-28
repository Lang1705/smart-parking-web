function formatRupiah(angka) {
    return 'Rp' + angka.toString().replace(/\B(?=(\d{3})+(?!\d))/g, '.');
}

function getAppContext() {
    const el = document.getElementById('appContext');
    if (!el) return { isMember: false, nama: '', hp: '', plat: '' };
    return {
        isMember: el.getAttribute('data-is-member') === 'true',
        nama: el.getAttribute('data-user-nama') || '',
        hp: el.getAttribute('data-user-hp') || '',
        plat: el.getAttribute('data-user-plat') || ''
    };
}

function pilihLantaiUser(nomorLantai) {
    const f1 = document.getElementById('userFloor_1');
    const f2 = document.getElementById('userFloor_2');
    const b1 = document.getElementById('btnTabLantai1');
    const b2 = document.getElementById('btnTabLantai2');
    if (!f1 || !f2) return;

    if (nomorLantai === 1) {
        f1.style.display = 'block';
        f2.style.display = 'none';
        if (b1) b1.classList.add('active');
        if (b2) b2.classList.remove('active');
    } else {
        f1.style.display = 'none';
        f2.style.display = 'block';
        if (b1) b1.classList.remove('active');
        if (b2) b2.classList.add('active');
    }
}

function updateTarifModal() {
    const durasiEl = document.getElementById('durasi');
    if (!durasiEl) return;

    const ctx = getAppContext();
    const durasi = parseInt(durasiEl.value, 10) || 1;
    const tarifNormal = durasi <= 1 ? 5000 : 5000 + (durasi - 1) * 3000;
    const diskon = ctx.isMember ? Math.floor(tarifNormal * 0.10) : 0;
    const totalAkhir = tarifNormal - diskon;

    const prevNormal = document.getElementById('previewTarifNormal');
    const prevDiskon = document.getElementById('previewDiskon');
    const prevHarga = document.getElementById('previewHarga');
    const payBig = document.getElementById('payTotalBig');

    if (prevNormal) prevNormal.textContent = formatRupiah(tarifNormal);
    if (prevDiskon) prevDiskon.textContent = '- ' + formatRupiah(diskon);
    if (prevHarga) prevHarga.textContent = formatRupiah(totalAkhir);
    if (payBig) payBig.textContent = formatRupiah(totalAkhir);
}

function pilihModePlat(mode) {
    const ctx = getAppContext();
    const inputPlat = document.getElementById('plat_nomor');
    const btnLama = document.getElementById('btnPlatLama');
    const btnBaru = document.getElementById('btnPlatBaru');
    if (!inputPlat) return;

    if (mode === 'lama') {
        inputPlat.value = ctx.plat;
        inputPlat.readOnly = true;
        if (btnLama) btnLama.classList.add('active');
        if (btnBaru) btnBaru.classList.remove('active');
    } else {
        inputPlat.value = '';
        inputPlat.readOnly = false;
        inputPlat.placeholder = 'Ketik plat kendaraan baru...';
        inputPlat.focus();
        if (btnLama) btnLama.classList.remove('active');
        if (btnBaru) btnBaru.classList.add('active');
    }
}

function bukaModalParkir(kodeSlot) {
    const modal = document.getElementById('modalParkir');
    if (!modal) return;

    const ctx = getAppContext();
    document.getElementById('slot_pilihan').value = kodeSlot;
    document.getElementById('modalTitle').textContent = 'Reservasi Slot ' + kodeSlot;
    document.getElementById('paySlotLabel').textContent = kodeSlot;

    kembaliKeData();
    if (ctx.isMember) {
        pilihModePlat('lama');
    }

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

function lanjutKePembayaran() {
    const nama = document.getElementById('nama_pengendara').value.trim();
    const hp = document.getElementById('no_hp_booking').value.trim();
    const plat = document.getElementById('plat_nomor').value.trim();

    if (!nama || !hp || !plat) {
        alert('Harap lengkapi Nama, Nomor HP, dan Plat Kendaraan terlebih dahulu.');
        return;
    }

    updateTarifModal();
    document.getElementById('stepData').style.display = 'none';
    document.getElementById('stepPayment').style.display = 'block';
    document.getElementById('modalStepTag').textContent = 'Langkah 2 dari 2 • Pembayaran';
}

function kembaliKeData() {
    const stepData = document.getElementById('stepData');
    const stepPay = document.getElementById('stepPayment');
    const tag = document.getElementById('modalStepTag');
    if (stepData) stepData.style.display = 'block';
    if (stepPay) stepPay.style.display = 'none';
    if (tag) tag.textContent = 'Langkah 1 dari 2 • Data Kendaraan';
}

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
        qrisBox.style.display = 'none';
        kasirBox.style.display = 'block';
    }
}

function bukaModalDetailTerisi(idData, kodeSlot, durasiJam, sisaWaktu, jamSelesai, tarif, isOwner, waktuHabis, platNomor) {
    const modal = document.getElementById('modalDetailTerisi');
    if (!modal) return;

    document.getElementById('detailSlotTitle').textContent = 'Slot Parkir ' + kodeSlot;
    document.getElementById('detailSlotKode').textContent = kodeSlot;
    document.getElementById('detailSlotSelesai').textContent = jamSelesai;
    document.getElementById('detailSlotSisa').textContent = sisaWaktu;

    const ownerSec = document.getElementById('detailOwnerSection');
    const otherSec = document.getElementById('detailOtherSection');

    if (isOwner) {
        ownerSec.style.display = 'block';
        otherSec.style.display = 'none';
        document.getElementById('detailOwnerPlat').textContent = platNomor;

        const formSelesai = document.getElementById('formOwnerSelesai');
        const btnBatal = document.getElementById('btnTriggerBatalDariDetail');

        if (waktuHabis) {
            formSelesai.style.display = 'block';
            document.getElementById('detailSelesaiId').value = idData;
            btnBatal.style.display = 'none';
        } else {
            formSelesai.style.display = 'none';
            btnBatal.style.display = 'block';
            btnBatal.onclick = function() {
                tutupModalDetailTerisi();
                bukaModalBatal(idData, kodeSlot, platNomor, tarif, sisaWaktu);
            };
        }
    } else {
        ownerSec.style.display = 'none';
        otherSec.style.display = 'block';
    }

    modal.classList.add('active');
}

function tutupModalDetailTerisi() {
    const modal = document.getElementById('modalDetailTerisi');
    if (modal) modal.classList.remove('active');
}

function bukaModalBatal(idData, kodeSlot, platNomor, tarif, sisaWaktu) {
    const modal = document.getElementById('modalBatal');
    if (!modal) return;

    document.getElementById('batalKeluarId').value = idData;
    document.getElementById('batalKodeSlot').textContent = kodeSlot;
    document.getElementById('batalPlat').textContent = platNomor;
    document.getElementById('batalNominal').textContent = tarif;
    document.getElementById('batalSisaWaktu').textContent = sisaWaktu;

    modal.classList.add('active');
}

function tutupModalBatal() {
    const modal = document.getElementById('modalBatal');
    if (modal) modal.classList.remove('active');
}

function updateLiveClock() {
    const dateEl = document.getElementById('liveDate');
    const clockEl = document.getElementById('liveClock');

    const now = new Date();
    const hari = ['Minggu', 'Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu'];
    const bulan = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'];

    if (dateEl) {
        dateEl.textContent = `${hari[now.getDay()]}, ${now.getDate()} ${bulan[now.getMonth()]} ${now.getFullYear()}`;
    }

    if (clockEl) {
        const hh = String(now.getHours()).padStart(2, '0');
        const mm = String(now.getMinutes()).padStart(2, '0');
        const ss = String(now.getSeconds()).padStart(2, '0');
        clockEl.textContent = `${hh}:${mm}:${ss} WIB`;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    updateLiveClock();
    setInterval(updateLiveClock, 1000);

    const adminRoot = document.getElementById('adminDashboardRoot');
    if (adminRoot) {
        setInterval(() => {
            window.location.href = '/';
        }, 10000);
    }
});
