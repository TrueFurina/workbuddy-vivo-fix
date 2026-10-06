import winreg, os, time

out = []
def w(s): out.append(str(s))

# 1. 注册表枚举驱动服务(绕开 driverquery/CIM 拦截)
netkw = ['npcap', 'vbox', 'todesk', 'oray', 'huorong', 'sysdiag', 'hips', 'winpcap',
         'pcap', 'wfp', 'ndis', 'filter', 'firewall', 'tencent', '360', 'ksoft',
         'ksafe', 'sangfor', 'qmp', 'qmprotector', 'lenovo', 'lnv']
startmap = {0: 'BOOT(内核启动即加载)', 1: 'SYSTEM', 2: 'AUTO(开机自启)',
            3: 'DEMAND(按需)', 4: 'DISABLED'}
try:
    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'SYSTEM\CurrentControlSet\Services')
    i = 0
    total = 0
    suspects = []
    while True:
        try:
            name = winreg.EnumKey(key, i)
        except OSError:
            break
        i += 1
        total += 1
        try:
            sk = winreg.OpenKey(key, name)
            def rv(k):
                try:
                    return winreg.QueryValueEx(sk, k)[0]
                except Exception:
                    return None
            typ, start, img, group = rv('Type'), rv('Start'), rv('ImagePath'), rv('Group')
            winreg.CloseKey(sk)
        except Exception:
            continue
        isdrv = typ in (1, 2, 4, 8) if typ is not None else False
        blob = (name + ' ' + str(img) + ' ' + str(group)).lower()
        if isdrv and any(k in blob for k in netkw):
            suspects.append((name, typ, start, group, img))
    w('=== 注册表驱动扫描 (共 %d 个服务键) ===' % total)
    w('--- 命中网络/过滤/安全关键字的第三方驱动 ---')
    if suspects:
        for n, t, s, g, im in suspects:
            w('  DRV %-26s start=%-20s group=%-10s img=%s' %
              (n, startmap.get(s, str(s)), str(g), str(im)[:100]))
    else:
        w('  (无命中)')
    winreg.CloseKey(key)
except Exception as e:
    w('registry scan err: ' + str(e))

# 2. NSIS 临时目录: 安装器是真卡还是在工作
td = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Temp')
w('--- NSIS 解压目录活动状态 ---')
found = 0
try:
    for name in os.listdir(td):
        if name.lower().startswith('ns') and name.lower().endswith('.tmp'):
            fp = os.path.join(td, name)
            age_min = (time.time() - os.path.getmtime(fp)) / 60
            try:
                fc = len(os.listdir(fp))
            except Exception:
                fc = -1
            w('  NSIS %s 最后改动=%.1f分钟前 文件数=%d %s' %
              (name, age_min, fc, '<-- 停滞(安装器卡死嫌疑)' if age_min > 3 else '<-- 活跃'))
            found += 1
except Exception as e:
    w('  nsis scan err ' + str(e))
if not found:
    w('  (无 NSIS 临时目录)')

# 3. qm-uninstall.log 尾部
qm = os.path.join(os.environ.get('USERPROFILE', ''), '.workbuddy', 'logs', 'update', 'qm-uninstall.log')
w('--- qm-uninstall.log 尾部30 ---')
try:
    lines = open(qm, encoding='utf-8', errors='ignore').read().splitlines()
    for l in lines[-30:]:
        w(l)
except Exception as e:
    w('  qm log err ' + str(e))

open(r'C:\Users\Lenovo\Desktop\wb_drv_scan.txt', 'w', encoding='utf-8').write('\n'.join(out))
print('\n'.join(out))
