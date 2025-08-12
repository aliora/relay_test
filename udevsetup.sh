#!/bin/bash
# MSR USB Relay için udev kuralları kurulum scripti

echo "🚀 MSR USB Relay için udev kuralları ekleniyor..."
echo "================================================"

# 1. Mevcut USB cihazlarını kontrol et
echo "1️⃣ USB cihazları kontrol ediliyor..."
lsusb | grep -E "(5131|1a86)" && echo "✅ MSR/CH340 cihazları tespit edildi" || echo "❓ MSR/CH340 cihazları bulunamadı"

# 2. Udev kuralları dosyasını oluştur
echo "2️⃣ Udev kuralları dosyası oluşturuluyor..."
sudo tee /etc/udev/rules.d/99-msr-relay.rules > /dev/null << 'EOF'
# MSR USB Relay - Vendor ID: 5131, Product ID: 2007
SUBSYSTEM=="usb", ATTR{idVendor}=="5131", ATTR{idProduct}=="2007", MODE="0666", GROUP="plugdev", TAG+="uaccess"

# CH340 USB to Serial - Vendor ID: 1a86, Product ID: 7523
SUBSYSTEM=="usb", ATTR{idVendor}=="1a86", ATTR{idProduct}=="7523", MODE="0666", GROUP="plugdev", TAG+="uaccess"

# MSR Reader alternatif kuralları (farklı ürün ID'leri için)
SUBSYSTEM=="usb", ATTR{idVendor}=="5131", MODE="0666", GROUP="plugdev", TAG+="uaccess"

# Tüm seri portlar için genel kural
KERNEL=="ttyUSB*", ATTRS{idVendor}=="1a86", ATTRS{idProduct}=="7523", MODE="0666", GROUP="dialout"
EOF

echo "✅ Udev kuralları dosyası oluşturuldu: /etc/udev/rules.d/99-msr-relay.rules"

# 3. Kullanıcıyı gerekli gruplara ekle
echo "3️⃣ Kullanıcı yetkileri ayarlanıyor..."
sudo usermod -a -G plugdev,dialout $USER
echo "✅ Kullanıcı ($USER) plugdev ve dialout gruplarına eklendi"

# 4. Udev kurallarını yeniden yükle
echo "4️⃣ Udev kuralları yeniden yükleniyor..."
sudo udevadm control --reload-rules
sudo udevadm trigger
echo "✅ Udev kuralları yenilendi"

# 5. Mevcut grup üyeliklerini göster
echo "5️⃣ Mevcut grup üyelikleri:"
groups $USER

# 6. Test komutu
echo ""
echo "📋 KURULUM TAMAMLANDI!"
echo "========================"
echo "✅ Udev kuralları eklendi"
echo "✅ Kullanıcı yetkileri ayarlandı"
echo ""
echo "🔄 ÖNEMLİ: Değişikliklerin etkili olması için:"
echo "   1. USB cihazını çıkarıp tekrar takın"
echo "   2. Terminali kapatıp yeniden açın (veya sistemi yeniden başlatın)"
echo ""
echo "🧪 TEST KOMUTLARI:"
echo "   # USB cihazlarını listele:"
echo "   lsusb | grep -E '(5131|1a86)'"
echo ""
echo "   # Cihaz izinlerini kontrol et:"
echo "   ls -la /dev/bus/usb/*/*"
echo ""
echo "   # Python scriptinizi çalıştırın (sudo olmadan)"
echo ""
echo "❓ SORUN GİDERME:"
echo "   - Hala 'Permission denied' hatası alıyorsanız sistemi yeniden başlatın"
echo "   - 'lsusb' komutunda cihazınızı göremiyorsanız USB bağlantısını kontrol edin"