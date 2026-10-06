import os, winreg, time

out = []
def w(s): out.append(str(s))

# 1. QmProtector 组件现场状态
pd = r'D:\WorkBuddy\resources\app.asar.unpacked\resources\plugins\workbuddy-builtin\builtin-plugins\weixinpay\prebuilds\win32-x64'
w('=== QmProtector 插件目录 ===')
w('  path: ' + pd)
w('  exists=' + str(os.path.exists(pd)))
if os.path.exists(pd):
    try:
        for f in os.listdir(pd):
            fp = os.path.join(pd, f)
            try:
                w('    %-28s %10d  %s' % (f, os.path.getsize(fp),
                  time.strftime('%m-%d %H:%M', time.localtime(os.path.getmtime(fp)))))
            except Exception:
                w('    ' + f)
    except Exception as e:
        w('  list err ' + str(e))
    disabled = pd + '_disabled_by_fix'
    w('  是否已有禁用副本: ' + str(os.path.exists(disabled)))

# 2. qm-helper.exe
qh = r'D:\WorkBuddy\resources\qm\qm-helper.exe'
w('=== qm-helper.exe ===')
w('  exists=' + str(os.path.exists(qh)))
if os.path.exists(qh):
    w('  size=%d mtime=%s' % (os.path.getsize(qh),
      time.strftime('%m-%d %H:%M', time.localtime(os.path.getmtime(qh)))))

# 3. 注册表里是否有 QmProtector 驱动服务
w('=== 注册表: 名字含 qm 的服务 ===')
try:
    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'SYSTEM\CurrentControlSet\Services')
    i = 0
    hits = []
    while True:
        try:
            n = winreg.EnumKey(key, i)
        except OSError:
            break
        i += 1
        if 'qm' in n.lower() or 'weixin' in n.lower() or 'wxpay' in n.lower():
            try:
                sk = winreg.OpenKey(key, n)
                try:
                    img = winreg.QueryValueEx(sk, 'ImagePath')[0]
                except Exception:
                    img = None
                try:
                    st = winreg.QueryValueEx(sk, 'Start')[0]
                except Exception:
                    st = None
                winreg.CloseKey(sk)
            except Exception:
                img, st = None, None
            hits.append((n, st, img))
    w('  ' + (str(hits) if hits else '无 (QmProtector 驱动未注册/未加载 -> 这正是 Initialize=0x80000002 的原因)'))
    winreg.CloseKey(key)
except Exception as e:
    w('  registry err ' + str(e))

# 4. 目标目录可写性(安装器要覆盖 D:\WorkBuddy)
w('=== D:\\WorkBuddy 可写性测试 ===')
tp = os.path.join(r'D:\WorkBuddy', '_wb_write_test.tmp')
try:
    with open(tp, 'w') as f:
        f.write('x')
    w('  写入测试: OK (目录未被独占锁定)')
    os.remove(tp)
    w('  清理测试文件: OK')
except Exception as e:
    w('  写入测试失败: ' + str(e))

open(r'C:\Users\Lenovo\Desktop\qm_check.txt', 'w', encoding='utf-8').write('\n'.join(out))
print('\n'.join(out))
