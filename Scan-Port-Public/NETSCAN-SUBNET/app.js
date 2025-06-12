const express = require('express');
const { exec } = require('child_process');
const bodyParser = require('body-parser');

const app = express();
const port = 36969;

const nmapPath = `"C:\\Program Files (x86)\\Nmap\\nmap.exe"`;

app.use(bodyParser.urlencoded({ extended: true }));
app.use(express.static(__dirname));

app.get('/', (req, res) => {
    res.sendFile(__dirname + '/index.html');
});

app.post('/scan', (req, res) => {
    const ip = req.body.ip;
    const scanType = req.body.scanType;
    const specifiedPort = req.body.specifiedPort;

    // Regex รองรับทั้ง IP เดี่ยวและ CIDR (เช่น 192.168.1.1 หรือ 192.168.1.0/24)
    const ipRegex = /^(?:\d{1,3}\.){3}\d{1,3}(?:\/\d{1,2})?$/;
    if (!ip || !ipRegex.test(ip)) {
        return res.status(400).json({ error: 'ที่อยู่ IP หรือ CIDR ไม่ถูกต้อง' });
    }

    const isCIDR = ip.includes('/');
    let command = '';

    if (scanType === 'all') {
        command = isCIDR 
            ? `${nmapPath} -p- -Pn -n -T4 ${ip} -oA nmap-scan` // สแกนทุกพอร์ตใน subnet
            : `${nmapPath} -p- -Pn -n -T4 ${ip} -oA nmap-scan`; // สแกนทุกพอร์ตใน IP เดี่ยว
    } else if (scanType === 'specified') {
        command = specifiedPort 
            ? `${nmapPath} -p ${specifiedPort} -O ${ip} -oA nmap-scan` 
            : `${nmapPath} -O ${ip} -oA nmap-scan`;
    } else if (scanType === 'quick') {
        command = isCIDR 
            ? `${nmapPath} -sn -T4 ${ip} -oA nmap-scan` // Quick scan สำหรับ subnet (ping scan)
            : `${nmapPath} -n -T4 ${ip} -oA nmap-scan`; // Quick scan สำหรับ IP เดี่ยว
    }

    exec(command, { encoding: 'utf8', timeout: 120000 }, (error, stdout, stderr) => {
        if (error) {
            console.error(`Error: ${error.message}`);
            console.error(`Stderr: ${stderr}`);
            return res.status(500).json({ error: `เกิดข้อผิดพลาดในการสแกน: ${error.message}` });
        }
        if (stderr) {
            console.error(`Nmap stderr: ${stderr}`);
        }

        const scanResults = parseNmapOutput(stdout, ip, scanType, isCIDR);
        res.json(scanResults);
    });
});

function parseNmapOutput(output, ip, scanType, isCIDR) {
    const lines = output.split('\n');
    let ports = [];
    let hosts = [];

    if (isCIDR) {
        // การสแกน subnet
        lines.forEach(line => {
            if (line.includes('Nmap scan report for')) {
                const hostMatch = line.match(/Nmap scan report for ([\d.]+)/);
                if (hostMatch) {
                    hosts.push({ ip: hostMatch[1], ports: [] });
                }
            }
            if (line.includes('open')) {
                const portMatch = line.match(/(\d+)\/tcp\s+open\s+(.+)/);
                if (portMatch && hosts.length > 0) {
                    hosts[hosts.length - 1].ports.push({
                        number: portMatch[1],
                        service: portMatch[2] || 'ไม่ทราบ',
                        status: 'open'
                    });
                }
            } else if (line.includes('closed')) {
                const portMatch = line.match(/(\d+)\/tcp\s+closed/);
                if (portMatch && hosts.length > 0) {
                    hosts[hosts.length - 1].ports.push({
                        number: portMatch[1],
                        service: 'ไม่ทราบ',
                        status: 'closed'
                    });
                }
            }
        });

        return {
            ip: ip,
            timestamp: new Date().toISOString(),
            scanType: scanType,
            hosts: hosts.length > 0 ? hosts : [{ ip: 'N/A', ports: [{ number: 'N/A', service: 'ไม่พบโฮสต์', status: 'closed' }] }]
        };
    } else {
        // การสแกน IP เดี่ยว
        lines.forEach(line => {
            if (line.includes('open')) {
                const portMatch = line.match(/(\d+)\/tcp\s+open\s+(.+)/);
                if (portMatch) {
                    ports.push({
                        number: portMatch[1],
                        service: portMatch[2] || 'ไม่ทราบ',
                        status: 'open'
                    });
                }
            } else if (line.includes('closed')) {
                const portMatch = line.match(/(\d+)\/tcp\s+closed/);
                if (portMatch) {
                    ports.push({
                        number: portMatch[1],
                        service: 'ไม่ทราบ',
                        status: 'closed'
                    });
                }
            }
        });

        return {
            ip: ip,
            timestamp: new Date().toISOString(),
            scanType: scanType,
            ports: ports.length > 0 ? ports : [{ number: 'N/A', service: 'ไม่พบพอร์ต', status: 'closed' }]
        };
    }
}

app.listen(port, () => {
    console.log(`Server is running on port ${port}`);
});