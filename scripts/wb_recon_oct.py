import os, subprocess, time, shutil, glob

out = []
def w(s): out.append(str(s))

# 1. 当前安装版本
for p in [r'D:\WorkBuddy\version', r'D:\WorkBuddy\resources\app.asar.unpacked\package.json']:
    if os.path.exists(p):
        try:
            txt = open(p, encoding='utf-8', errors='ignore').read()[:400]
            w(f"VERFILE {p}: {txt.strip()[:200]}")
        except Exception as e:
            w(f"VERFILE {p} err {e}")
    else:
        w(f"VERFILE {p}: missing")

# 2. 待装更新包
pkgdir = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Temp', 'workbuddy-update-x64')
w('PKGDIR: ' + pkgdir + ' exists=' + str(os.path.exists(pkgdir)))
if os.path.exists(pkgdir):
    for n in os.listdir(pkgdir):
        fp = os.path.join(pkgdir, n)
        try:
            w('  PKG %s size=%d mtime=%s' % (n, os.path.getsize(fp),
              time.strftime('%m-%d %H:%M', time.localtime(os.path.getmtime(fp)))))
        except Exception as e:
            w('  PKG %s err %s' % (n, e))

# 3. 更新日志目录 + 最新日志尾部
logdir = os.path.join(os.environ.get('USERPROFILE', ''), '.workbuddy', 'logs', 'update')
w('LOGDIR: ' + logdir + ' exists=' + str(os.path.exists(logdir)))
if os.path.exists(logdir):
    files = sorted(glob.glob(os.path.join(logdir, '*')), key=os.path.getmtime, reverse=True)[:5]
    for f in files:
        w('  LOG %s mtime=%s size=%d' % (os.path.basename(f),
          time.strftime('%m-%d %H:%M', time.localtime(os.path.getmtime(f))), os.path.getsize(f)))
    if files:
        newest = files[0]
        w('=== TAIL of %s (last 70 lines) ===' % os.path.basename(newest))
        try:
            lines = open(newest, encoding='utf-8', errors='ignore').read().splitlines()
            for l in lines[-70:]:
                w(l)
        except Exception as e:
            w('tail err ' + str(e))

# 4. 防火墙健康检查(关键: 9月定位的死锁是否还在)
w('--- FW TEST (netsh advfirewall, 10s timeout) ---')
t0 = time.time()
try:
    p = subprocess.run(['netsh', 'advfirewall', 'show', 'allprofiles', 'state'],
                       capture_output=True, timeout=10)
    w('FW exit=%s elapsed=%.1fs  -> 防火墙正常响应' % (p.returncode, time.time() - t0))
except subprocess.TimeoutExpired:
    w('FW HANG (>%.1fs) -> MpsSvc/BFE 仍死锁(9月根因未除)' % (time.time() - t0))
except Exception as e:
    w('FW err ' + str(e))

# 5. 进程
try:
    txt = subprocess.run(['tasklist', '/FO', 'CSV'], capture_output=True).stdout.decode('gbk', 'ignore')
    hits = [l for l in txt.splitlines() if 'WorkBuddy-Setup' in l or 'nsis' in l.lower()]
    w('INSTALLER PROCS: ' + str(hits if hits else 'none'))
    wbcount = sum(1 for l in txt.splitlines() if '"WorkBuddy.exe"' in l)
    w('WB PROC COUNT: %d' % wbcount)
except Exception as e:
    w('tasklist err ' + str(e))

# 6. 磁盘
for d in ['C:\\', 'D:\\']:
    try:
        tp = shutil.disk_usage(d)
        w('DISK %s free=%.1fGB used=%.0f%%' % (d, tp.free / 1e9, tp.used * 100 / tp.total))
    except Exception as e:
        w('DISK %s err %s' % (d, e))

open(r'C:\Users\Lenovo\Desktop\wb_recon_oct.txt', 'w', encoding='utf-8').write('\n'.join(out))
print('\n'.join(out))
