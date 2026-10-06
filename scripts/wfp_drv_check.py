import winreg as reg

targets = {
    'uunetfilter':   'NetFilter SDK WFP 驱动(本次真凶)',
    'npcap':         'Npcap (Wireshark/Nmap 抓包)',
    'VBoxNetLwf':    'VirtualBox 桥接网络过滤',
    'lnvscenter':    '火绒/Huorong 网络过滤',
    'fse':           '微软 Flow Steering Engine(自家, 排除)',
    'hnswfpdriver':  '微软 HNS(自家, 排除)',
}
base = r'SYSTEM\CurrentControlSet\Services'

def qget(k, name):
    try:
        return reg.QueryValueEx(k, name)[0]
    except OSError:
        return None

print('=== 当前驱动启动类型 (start: 0=boot 1=system 2=auto 3=demand 4=disabled) ===')
for name, desc in targets.items():
    try:
        k = reg.OpenKey(reg.HKEY_LOCAL_MACHINE, base + '\\' + name)
        start = qget(k, 'Start')
        typ = qget(k, 'Type')
        img = qget(k, 'ImagePath')
        grp = qget(k, 'Group')
        print('  %-14s start=%s type=%s grp=%r %s' % (name, start, typ, grp, desc))
        print('       ImagePath=%s' % img)
        reg.CloseKey(k)
    except FileNotFoundError:
        print('  %-14s (无此项/未安装)  %s' % (name, desc))

print()
print('=== 所有 start<=1 且分组是网络过滤类的驱动 ===')
cnt = 0
hk = reg.OpenKey(reg.HKEY_LOCAL_MACHINE, base)
i = 0
while True:
    try:
        svc = reg.EnumKey(hk, i); i += 1
    except OSError:
        break
    try:
        sk = reg.OpenKey(hk, svc)
        start = qget(sk, 'Start')
        grp = qget(sk, 'Group') or ''
        reg.CloseKey(sk)
        if start in (0, 1) and any(t in grp.lower() for t in ['ndis', 'pnp_tdi', 'filter', 'wfp', 'net']):
            print('  %-18s start=%s grp=%s' % (svc, start, grp))
            cnt += 1
    except Exception:
        pass
reg.CloseKey(hk)
if cnt == 0:
    print('  (未匹配到额外项)')
