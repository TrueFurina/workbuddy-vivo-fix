import winreg as reg, os, subprocess

# 1) 查 uunetfilter 服务的 DisplayName / Description / 依赖
def qget(k, name):
    try:
        return reg.QueryValueEx(k, name)[0]
    except OSError:
        return None

for svc in ['uunetfilter', 'lnvscenter', 'VBoxNetLwf', 'npcap']:
    try:
        k = reg.OpenKey(reg.HKEY_LOCAL_MACHINE, r'SYSTEM\CurrentControlSet\Services\\' + svc)
        print('=== %s ===' % svc)
        print('  DisplayName :', qget(k, 'DisplayName'))
        print('  Description :', qget(k, 'Description'))
        print('  DependOnService:', qget(k, 'DependOnService'))
        print('  ImagePath   :', qget(k, 'ImagePath'))
        reg.CloseKey(k)
    except FileNotFoundError:
        print('=== %s === 未安装' % svc)

# 2) uunetfilter.sys 文件厂商
syspath = r'C:\Windows\System32\drivers\uunetfilter.sys'
if os.path.exists(syspath):
    try:
        out = subprocess.run(
            ['powershell', '-NoProfile', '-Command',
             "(Get-Item '%s').VersionInfo | Select-Object CompanyName,FileDescription,ProductName,ProductVersion | Format-List | Out-String" % syspath],
            capture_output=True, text=True, timeout=20)
        print('--- uunetfilter.sys 厂商 ---')
        print(out.stdout.strip() or out.stderr.strip())
    except Exception as e:
        print('ps getver err:', e)

# 3) 注册表里搜 NetFilter / uunetfilter 指向的卸载项或程序名
print('--- 注册表搜索 NetFilter 相关安装痕迹 ---')
roots = [
    (reg.HKEY_LOCAL_MACHINE, r'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall'),
    (reg.HKEY_LOCAL_MACHINE, r'SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall'),
    (reg.HKEY_CURRENT_USER, r'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall'),
]
hits = {}
for hk, sub in roots:
    try:
        h = reg.OpenKey(hk, sub)
    except OSError:
        continue
    i = 0
    while True:
        try:
            key = reg.EnumKey(h, i); i += 1
        except OSError:
            break
        try:
            sk = reg.OpenKey(h, key)
            disp = qget(sk, 'DisplayName')
            loc = qget(sk, 'InstallLocation')
            reg.CloseKey(sk)
            blob = ' '.join(str(x) for x in [disp, loc] if x)
            if blob and any(t in blob.lower() for t in ['netfilter', 'uunet', 'uu', 'netpas', 'vpn', 'proxi', '加速器', 'filter']):
                hits[key] = blob
        except Exception:
            pass
    reg.CloseKey(h)
if hits:
    for kk, vv in hits.items():
        print('  命中:', kk, '->', vv)
else:
    print('  未直接匹配到安装项 (NetFilter SDK 多被第三方app静默打包, 名字不一定含 NetFilter)')
