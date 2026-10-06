import os, time, subprocess, glob

out = []
def w(s): out.append(str(s))

# 1. D:\WorkBuddy 最近被修改的文件 —— 判断安装器究竟走到第几步
wb = r'D:\WorkBuddy'
rows = []
count = 0
for root, dirs, files in os.walk(wb):
    for f in files:
        p = os.path.join(root, f)
        try:
            rows.append((os.path.getmtime(p), p, os.path.getsize(p)))
        except Exception:
            pass
        count += 1
    if count > 6000:
        break
rows.sort(reverse=True)
w('=== D:\\WorkBuddy 最近修改的 20 个文件 ===')
for mt, p, sz in rows[:20]:
    w('  %s  %10d  %s' % (time.strftime('%m-%d %H:%M:%S', time.localtime(mt)), sz, p[len(wb):]))

oldest_recent = rows[0][0] if rows else 0
w('  最新改动时间: %s (距今 %.1f 分钟)' % (
    time.strftime('%m-%d %H:%M:%S', time.localtime(oldest_recent)),
    (time.time() - oldest_recent) / 60))
w('  >>> 若最新改动远早于 00:02(本次安装尝试), 说明安装器根本没开始写文件 = 卡在写文件之前')

# 2. NSIS 临时目录里到底解压了什么
td = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Temp')
w('--- NSIS 临时目录内容 ---')
for name in os.listdir(td):
    if name.lower().startswith('ns') and name.lower().endswith('.tmp'):
        fp = os.path.join(td, name)
        try:
            fs = os.listdir(fp)
            age = (time.time() - os.path.getmtime(fp)) / 60
            w('  %s (%.1f分钟前, 文件数=%d): %s' % (name, age, len(fs), fs))
        except Exception as e:
            w('  %s err %s' % (name, e))

# 3. 卸载器/安装残留: D:\WorkBuddy 是否有 .old/.tmp 半成品
w('--- D:\\WorkBuddy 根目录是否有安装残留 ---')
try:
    top = os.listdir(wb)
    suspects = [x for x in top if any(k in x.lower() for k in ['.old', '.tmp', '.bak', 'uninst', '.new', 'update'])]
    w('  残留候选: %s' % (suspects if suspects else '无'))
except Exception as e:
    w('  err ' + str(e))

# 4. 当前进程: 是否还有 WB 残留子进程(安装器可能在等它们退出)
try:
    txt = subprocess.run(['tasklist', '/FO', 'CSV'], capture_output=True).stdout.decode('gbk', 'ignore')
    wbp = [l for l in txt.splitlines() if '"WorkBuddy.exe"' in l]
    inst = [l for l in txt.splitlines() if 'WorkBuddy-Setup' in l]
    w('--- 进程 ---')
    w('  WorkBuddy.exe 数量: %d' % len(wbp))
    w('  安装器进程: %s' % (inst if inst else '无'))
    # 找 wb 的子进程/辅助进程
    others = [l for l in txt.splitlines() if any(k in l for k in ['qm-helper', 'qm-uninstall', 'sidecar', 'wscript'])]
    w('  辅助进程(qm/sidecar/wscript): %s' % (others if others else '无'))
except Exception as e:
    w('tasklist err ' + str(e))

open(r'C:\Users\Lenovo\Desktop\wb_step.txt', 'w', encoding='utf-8').write('\n'.join(out))
print('\n'.join(out))
