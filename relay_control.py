import usb.core
import usb.util
import serial
import serial.tools.list_ports
import time
import sys
import subprocess
import re

# GLOBAL: Sabit değerler
RELAY_DELAY = 1  # seconds

# CLASS: Röle komut yapısı
class RelayCommands:
    RELAY_COMMANDS = {
        1: {"on": b'\xA0\x01\x01\xA2', "off": b'\xA0\x01\x00\xA1'}
    }

def get_lsusb_order():
    """lsusb çıktısına göre USB cihazlarının sırasını alır"""
    try:
        result = subprocess.run(['lsusb'], capture_output=True, text=True, check=True)
        lines = result.stdout.strip().split('\n')
        
        usb_devices = []
        for line in lines:
            # lsusb formatı: Bus 001 Device 003: ID 1a86:7523 QinHeng Electronics HL-340 USB-Serial adapter
            match = re.search(r'Bus (\d+) Device (\d+): ID ([0-9a-f]{4}):([0-9a-f]{4})', line)
            if match:
                bus = int(match.group(1))
                device = int(match.group(2))
                vendor_id = int(match.group(3), 16)
                product_id = int(match.group(4), 16)
                
                usb_devices.append({
                    'bus': bus,
                    'device': device,
                    'vendor_id': vendor_id,
                    'product_id': product_id,
                    'line': line
                })
        
        return usb_devices
    except Exception as e:
        print(f"lsusb komutu çalıştırılamadı: {e}")
        return []

def find_usb_devices_ordered(device_list):
    """lsusb sırasına göre USB cihazlarını bulur ve sıralar"""
    found_devices = {}
    lsusb_devices = get_lsusb_order()
    
    for device_name, (vendor_id, product_id) in device_list.items():
        # lsusb sırasına göre eşleşen cihazları bul
        matching_lsusb = [d for d in lsusb_devices 
                         if d['vendor_id'] == vendor_id and d['product_id'] == product_id]
        
        if matching_lsusb:
            # Bus ve device numarasına göre sırala (lsusb sırası)
            matching_lsusb.sort(key=lambda x: (x['bus'], x['device']))
            
            # USB cihazlarını pyusb ile bul ve lsusb sırasına göre eşleştir
            pyusb_devices = list(usb.core.find(find_all=True, idVendor=vendor_id, idProduct=product_id))
            
            ordered_devices = []
            for lsusb_dev in matching_lsusb:
                # pyusb cihazını bus ve device numarasına göre eşleştir
                for pyusb_dev in pyusb_devices:
                    if (pyusb_dev.bus == lsusb_dev['bus'] and 
                        pyusb_dev.address == lsusb_dev['device']):
                        ordered_devices.append(pyusb_dev)
                        break
            
            if ordered_devices:
                found_devices[device_name] = ordered_devices
                print(f"Bulundu {len(ordered_devices)} adet {device_name} (lsusb sırasına göre)")
                for i, dev in enumerate(ordered_devices, 1):
                    lsusb_info = matching_lsusb[i-1]
                    print(f"  {device_name}_{i}: Bus {lsusb_info['bus']:03d} Device {lsusb_info['device']:03d} - {dev}")
        else:
            print(f"{device_name} bulunamadı")
    
    return found_devices

def find_ch340_ports_ordered():
    """CH340 portlarını lsusb sırasına göre bulur"""
    lsusb_devices = get_lsusb_order()
    
    # CH340 cihazlarını lsusb sırasına göre bul
    ch340_lsusb = [d for d in lsusb_devices 
                   if d['vendor_id'] == 0x1a86 and d['product_id'] == 0x7523]
    
    if not ch340_lsusb:
        return []
    
    # Bus ve device numarasına göre sırala
    ch340_lsusb.sort(key=lambda x: (x['bus'], x['device']))
    
    # Seri portları bul
    ports = serial.tools.list_ports.comports()
    ch340_ports = [port for port in ports 
                   if port.vid == 0x1a86 and port.pid == 0x7523]
    
    if len(ch340_ports) != len(ch340_lsusb):
        print(f"Uyarı: lsusb'da {len(ch340_lsusb)} CH340, seri portlarda {len(ch340_ports)} CH340 bulundu")
    
    # Port eşleştirme - bu kısım sisteme göre değişebilir
    # Genellikle USB sırası ile port sırası aynıdır ama garanti değil
    ordered_ports = []
    
    # Port isimlerine göre sıralama dene (genellikle /dev/ttyUSB0, /dev/ttyUSB1, ...)
    ch340_ports.sort(key=lambda p: p.device)
    
    for i, lsusb_dev in enumerate(ch340_lsusb):
        if i < len(ch340_ports):
            port = ch340_ports[i]
            ordered_ports.append({
                'port': port.device,
                'lsusb_info': lsusb_dev,
                'description': port.description
            })
            print(f"CH340_{i+1}: {port.device} - Bus {lsusb_dev['bus']:03d} Device {lsusb_dev['device']:03d}")
    
    return ordered_ports

def control_relay_device(device, relay_commands, device_type="CH340", device_index=0):
    try:
        if device_type == "CH340":
            # INIT: Sıralı port listesi
            ordered_ports = find_ch340_ports_ordered()
            
            if not ordered_ports:
                print("CH340 seri portu bulunamadı")
                return False
            
            if device_index >= len(ordered_ports):
                print(f"CH340 cihaz index {device_index} bulunamadı. Mevcut cihaz sayısı: {len(ordered_ports)}")
                return False
                
            target_port_info = ordered_ports[device_index]
            target_port = target_port_info['port']
            lsusb_info = target_port_info['lsusb_info']
            
            print(f"CH340 Converter #{device_index + 1} seçildi: {target_port}")
            print(f"  Bus {lsusb_info['bus']:03d} Device {lsusb_info['device']:03d}")
                
            # CONNECT: Seri port
            with serial.Serial(target_port, baudrate=9600, timeout=1) as ser:
                # CMD: Röle aç
                ser.write(relay_commands[1]["on"])
                print(f"CH340 Converter #{device_index + 1} röle açıldı: {relay_commands[1]['on'].hex()}")
                
                # Belirlenen süre kadar bekle
                print(f"Röle {RELAY_DELAY} saniye açık kalacak...")
                time.sleep(RELAY_DELAY)
                
                # CMD: Röle kapat
                ser.write(relay_commands[1]["off"])
                print(f"CH340 Converter #{device_index + 1} röle kapatıldı: {relay_commands[1]['off'].hex()}")
                return True
                
        elif device_type == "MSR":
            try:
                # Eğer birden fazla MSR cihazı varsa, belirtilen index'i seç
                if isinstance(device, list):
                    if device_index >= len(device):
                        print(f"MSR cihaz index {device_index} bulunamadı. Mevcut cihaz sayısı: {len(device)}")
                        return False
                    selected_device = device[device_index]
                    print(f"MSR Reader #{device_index + 1} seçildi")
                    print(f"  Bus {selected_device.bus:03d} Device {selected_device.address:03d}")
                else:
                    selected_device = device
                    print("MSR Reader seçildi")
                
                # INIT: USB reset
                selected_device.reset()
                
                # CONFIG: Driver ayarları
                for interface in [0, 1]:
                    if selected_device.is_kernel_driver_active(interface):
                        selected_device.detach_kernel_driver(interface)
                
                # CONFIG: USB ayarları
                selected_device.set_configuration()
                usb.util.claim_interface(selected_device, 0)
                
                # INIT: Endpoint bulma
                cfg = selected_device.get_active_configuration()
                intf = cfg[(0,0)]
                ep = usb.util.find_descriptor(
                    intf,
                    custom_match = \
                    lambda e: \
                        usb.util.endpoint_direction(e.bEndpointAddress) == \
                        usb.util.ENDPOINT_OUT
                )
                
                if ep is None:
                    raise RuntimeError('MSR Endpoint bulunamadı')
                
                # CMD: Röle aç
                ep.write(relay_commands[1]["on"])
                print(f"MSR Reader #{device_index + 1} röle açıldı: {relay_commands[1]['on'].hex()}")
                
                # Belirlenen süre kadar bekle
                print(f"Röle {RELAY_DELAY} saniye açık kalacak...")
                time.sleep(RELAY_DELAY)
                
                # CMD: Röle kapat
                ep.write(relay_commands[1]["off"])
                print(f"MSR Reader #{device_index + 1} röle kapatıldı: {relay_commands[1]['off'].hex()}")
                return True
                
            except usb.core.USBError as e:
                if e.errno == 16:
                    print("Cihaz meşgul. Yeniden bağlamayı deneyin veya:")
                    print("1. lsusb ile cihazı kontrol edin")
                    print("2. sudo rmmod usbserial")
                    print("3. Cihazı çıkarıp tekrar takın")
                elif e.errno == 13:
                    print("Yetki hatası: USB cihazına erişim için root yetkisi gerekiyor")
                    print("udev kurallarını eklediğinizden emin olun")
                else:
                    print(f"MSR USB hatası: {e}")
                return False
            
    except Exception as e:
        print(f"{device_type} röle kontrolünde hata: {e}")
        return False

def trigger_specific_relay(relay_number):
    """
    Belirtilen relay numarasına göre ilgili cihazı tetikler.
    relay_number: 1-4 arası değer
    """
    target_devices = {
        "MSR_Reader": (0x5131, 0x2007),
        "CH340_Converter": (0x1a86, 0x7523),
    }
    
    print(f"Relay #{relay_number} tetikleniyor...")
    print("USB cihazları lsusb sırasına göre taranıyor...")
    
    # lsusb çıktısını göster
    print("\n=== lsusb Çıktısı ===")
    try:
        subprocess.run(['lsusb'], check=True)
    except:
        pass
    print("====================\n")
    
    found_usb_devices = find_usb_devices_ordered(target_devices)
    print("Tarama tamamlandı.")
    
    # Tüm cihazları say
    total_devices = 0
    device_mapping = []
    
    # MSR cihazlarını ekle
    if "MSR_Reader" in found_usb_devices:
        msr_devices = found_usb_devices["MSR_Reader"]
        for i in range(len(msr_devices)):
            total_devices += 1
            device_mapping.append(("MSR", i))
            print(f"Cihaz {total_devices}: MSR Reader #{i + 1}")
    
    # CH340 cihazlarını ekle
    ordered_ports = find_ch340_ports_ordered()
    for i in range(len(ordered_ports)):
        total_devices += 1
        device_mapping.append(("CH340", i))
        print(f"Cihaz {total_devices}: CH340 Converter #{i + 1}")
    
    if total_devices == 0:
        print("Hiçbir relay cihazı bulunamadı!")
        return False
    
    print(f"Toplam {total_devices} relay cihazı bulundu.")
    
    # Relay numarasını kontrol et
    if relay_number < 1 or relay_number > total_devices:
        print(f"Geçersiz relay numarası: {relay_number}. Mevcut aralık: 1-{total_devices}")
        return False
    
    # Belirtilen relay'i tetikle
    device_type, device_index = device_mapping[relay_number - 1]
    
    if device_type == "MSR":
        return control_relay_device(found_usb_devices["MSR_Reader"], RelayCommands.RELAY_COMMANDS, device_type="MSR", device_index=device_index)
    elif device_type == "CH340":
        # CH340 için device parametresi kullanılmıyor, sadece index önemli
        return control_relay_device([], RelayCommands.RELAY_COMMANDS, device_type="CH340", device_index=device_index)
    
    return False

def list_all_devices():
    """Tüm cihazları listeler - test için"""
    print("=== Tüm USB Relay Cihazları ===")
    
    target_devices = {
        "MSR_Reader": (0x5131, 0x2007),
        "CH340_Converter": (0x1a86, 0x7523),
    }
    
    print("\n=== lsusb Çıktısı ===")
    try:
        subprocess.run(['lsusb'], check=True)
    except:
        pass
    print("====================\n")
    
    found_usb_devices = find_usb_devices_ordered(target_devices)
    
    # MSR cihazları
    device_counter = 1
    if "MSR_Reader" in found_usb_devices:
        print("MSR Reader Cihazları:")
        for i, device in enumerate(found_usb_devices["MSR_Reader"]):
            print(f"  Relay #{device_counter}: MSR Reader #{i + 1}")
            print(f"    Bus {device.bus:03d} Device {device.address:03d}")
            device_counter += 1
    
    # CH340 cihazları
    ordered_ports = find_ch340_ports_ordered()
    if ordered_ports:
        print("CH340 Converter Cihazları:")
        for i, port_info in enumerate(ordered_ports):
            print(f"  Relay #{device_counter}: CH340 Converter #{i + 1}")
            print(f"    Port: {port_info['port']}")
            print(f"    Bus {port_info['lsusb_info']['bus']:03d} Device {port_info['lsusb_info']['device']:03d}")
            device_counter += 1
    
    print(f"\nToplam {device_counter - 1} relay cihazı bulundu.")

# ==============================
# RelayControl Wrapper Class
# ==============================
class RelayControl:
    def __init__(self, brand=None):
        self.brand = brand or "CH340"
        self.commands = RelayCommands.RELAY_COMMANDS

    def triggerRelays(self, ip=None, port=None, relayNumber=None, duration=None):
        """JavaScript API'si ile uyumlu method"""
        if relayNumber:
            return trigger_specific_relay(relayNumber)
        else:
            return self.trigger()

    def trigger(self, device_type=None):
        """Eski API ile uyumluluk için"""
        device_type = device_type or self.brand
        target_devices = {
            "MSR_Reader": (0x5131, 0x2007),
            "CH340_Converter": (0x1a86, 0x7523),
        }
        found_devices = find_usb_devices_ordered(target_devices)
        if device_type == "MSR" and "MSR_Reader" in found_devices:
            return control_relay_device(found_devices["MSR_Reader"], self.commands, device_type="MSR", device_index=0)
        elif device_type in ["CH340", "MSR-CH340"]:
            return control_relay_device([], self.commands, device_type="CH340", device_index=0)
        return False

if __name__ == "__main__":
    # Komut satırı argümanını kontrol et
    if len(sys.argv) > 1:
        if sys.argv[1] == "--list" or sys.argv[1] == "-l":
            # Tüm cihazları listele
            list_all_devices()
        else:
            try:
                relay_number = int(sys.argv[1])
                print(f"Komut satırından alınan relay numarası: {relay_number}")
                success = trigger_specific_relay(relay_number)
                if success:
                    print(f"Relay #{relay_number} başarıyla tetiklendi!")
                else:
                    print(f"Relay #{relay_number} tetiklenemedi!")
                    sys.exit(1)
            except ValueError:
                print("Geçersiz relay numarası! Lütfen 1-4 arası bir sayı girin.")
                print("Veya tüm cihazları listelemek için --list kullanın.")
                sys.exit(1)
    else:
        # Argüman yoksa eski davranış - tüm cihazları tetikle
        target_devices = {
            "MSR_Reader": (0x5131, 0x2007),
            "CH340_Converter": (0x1a86, 0x7523),
        }
        
        print("USB cihazları taranıyor...")
        found_usb_devices = find_usb_devices_ordered(target_devices)
        print("Tarama tamamlandı.")
        
        # Bulunan cihazları kontrol et ve ilgili tetik kodlarını çalıştır
        for device_name, devices in found_usb_devices.items():
            if device_name == "MSR_Reader":
                print("MSR Reader cihazları tetikleniyor...")
                for i in range(len(devices)):
                    print(f"MSR Reader #{i + 1}")
                    control_relay_device(devices, RelayCommands.RELAY_COMMANDS, device_type="MSR", device_index=i)
                    time.sleep(0.5)  # Cihazlar arası bekleme
            elif device_name == "CH340_Converter":
                print("CH340 Converter cihazları tetikleniyor...")
                ordered_ports = find_ch340_ports_ordered()
                for i in range(len(ordered_ports)):
                    print(f"CH340 Converter #{i + 1}")
                    control_relay_device([], RelayCommands.RELAY_COMMANDS, device_type="CH340", device_index=i)
                    time.sleep(0.5)  # Cihazlar arası bekleme

        # Hiçbir cihaz bulunamazsa uyarı
        if not found_usb_devices:
            print("Hiçbir cihaz bulunamadı")