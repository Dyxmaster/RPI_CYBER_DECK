// static/js/main.js

// 把秒数格式化成 "1d 02:03:04" 这种
function formatUptime(seconds) {
    seconds = Math.max(0, Math.floor(seconds || 0));
    const days = Math.floor(seconds / 86400);
    const hrs  = Math.floor((seconds % 86400) / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;

    const hms = [
        String(hrs).padStart(2, '0'),
        String(mins).padStart(2, '0'),
        String(secs).padStart(2, '0'),
    ].join(':');

    if (days > 0) {
        return `${days}d ${hms}`;
    }
    return hms;
}

// 安全获取元素
function $(id) {
    return document.getElementById(id);
}

// 追加日志
function appendLogLine(message) {
    const box = $('log-box');
    if (!box) return;
    const line = document.createElement('div');
    line.className = 'log-line';
    const now = new Date();
    const timeStr = now.toLocaleTimeString();
    line.textContent = `[${timeStr}] ${message}`;
    // 最新在最上面
    box.prepend(line);

    // 最多保留 50 行
    while (box.children.length > 50) {
        box.removeChild(box.lastChild);
    }
}

// 更新整个面板
function updateUI(stats) {
    if (!stats) return;

    const cpu = stats.cpu || {};
    const mem = stats.memory || {};
    const disk = stats.disk || {};
    const sys = stats.system || {};

    // ===== 温度 =====
    if ($('temp-val')) {
        const t = sys.temp ?? 0;
        $('temp-val').textContent = t.toFixed ? t.toFixed(1) : t;
        const tempPercent = Math.max(0, Math.min(100, (t / 80) * 100)); // 假定 80°C 以上算 100%
        if ($('temp-bar')) {
            $('temp-bar').style.width = tempPercent + '%';
        }
    }

    // ===== CPU =====
    if ($('cpu-val')) {
        const cpuUsage = cpu.usage ?? 0;
        $('cpu-val').textContent = cpuUsage.toFixed(1);
        if ($('cpu-bar')) {
            $('cpu-bar').style.width = cpuUsage + '%';
        }
    }
    if ($('cpu-freq')) {
        $('cpu-freq').textContent = cpu.freq || '--';
    }
    if ($('cpu-cores')) {
        $('cpu-cores').textContent = cpu.cores ?? '--';
    }
    if ($('cpu-freq-small')) {
        $('cpu-freq-small').textContent = (cpu.freq || '--') + ' MHz';
    }

    // ===== 内存 =====
    if ($('mem-val')) {
        const mp = mem.percent ?? 0;
        $('mem-val').textContent = mp.toFixed ? mp.toFixed(1) : mp;
        if ($('mem-bar')) {
            $('mem-bar').style.width = mp + '%';
        }
    }
    if ($('mem-used'))  $('mem-used').textContent  = mem.used  ?? '--';
    if ($('mem-total')) $('mem-total').textContent = mem.total ?? '--';

    // 小摘要
    if ($('mem-used-small'))   $('mem-used-small').textContent   = mem.used  ?? '--';
    if ($('mem-total-small'))  $('mem-total-small').textContent  = mem.total ?? '--';
    if ($('mem-percent-small'))$('mem-percent-small').textContent = mem.percent ?? '--';

    // ===== 磁盘 =====
    if ($('disk-val')) {
        $('disk-val').textContent = (disk.percent ?? 0).toFixed
            ? disk.percent.toFixed(1) + '%'
            : disk.percent + '%';
    }
    if ($('disk-free')) $('disk-free').textContent = disk.free ?? '--';

    if ($('disk-percent-small')) $('disk-percent-small').textContent = disk.percent ?? '--';
    if ($('disk-free-small'))    $('disk-free-small').textContent    = disk.free    ?? '--';

    const diskCircle = $('disk-circle');
    if (diskCircle && typeof disk.percent === 'number') {
        const p = Math.max(0, Math.min(100, disk.percent));
        diskCircle.setAttribute('stroke-dasharray', `${p}, 100`);
    }

    // ===== 系统信息 =====
    if ($('sys-hostname')) $('sys-hostname').textContent = sys.hostname || '--';
    if ($('sys-ip'))       $('sys-ip').textContent       = sys.ip       || '--';
    if ($('sys-os'))       $('sys-os').textContent       = sys.os       || '--';

    const uptimeStr = formatUptime(sys.uptime);
    if ($('sys-uptime')) $('sys-uptime').textContent = uptimeStr;

    // 同步到导航栏小 HUD
    if ($('nav-host-name')) $('nav-host-name').textContent = sys.hostname || 'NODE-01';
    if ($('nav-uptime'))    $('nav-uptime').textContent    = uptimeStr;

    // 网络页：当前 IP
    if ($('ip-addr')) {
        $('ip-addr').textContent = sys.ip || 'Unknown';
    }

    // 写一条日志
    appendLogLine(
        `OK: CPU ${cpu.usage?.toFixed ? cpu.usage.toFixed(1) : cpu.usage || 0}% | ` +
        `Mem ${mem.percent ?? 0}% | Disk ${disk.percent ?? 0}%`
    );
}

// 定时拉取数据
async function fetchAndUpdate() {
    try {
        const res = await fetch('/api/system/stats');
        if (!res.ok) {
            throw new Error('HTTP ' + res.status);
        }
        const data = await res.json();
        updateUI(data);
    } catch (err) {
        console.error(err);
        appendLogLine('ERROR: ' + err.message);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    // 初始拉一次
    fetchAndUpdate();
    // 每 3 秒刷新一次
    setInterval(fetchAndUpdate, 3000);
});
