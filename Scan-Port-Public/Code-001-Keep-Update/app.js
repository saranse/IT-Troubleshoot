const express = require('express');
const { exec } = require('child_process');
const bodyParser = require('body-parser');
const path = require('path');

// �ѧ�Ѻ��� Node.js �� UTF-8
process.env.NODE_ICU_DATA = 'node_modules/full-icu';

const app = express();
const port = 36969;

const nmapPath = `"C:\\Program Files (x86)\\Nmap\\nmap.exe"`;

app.use(bodyParser.urlencoded({ extended: true }));
app.use(express.static(__dirname));

// �����˹�� version ���� (index.html)
app.get('/', (req, res) => {
    res.setHeader('Content-Type', 'text/html; charset=utf-8');
    res.sendFile(path.join(__dirname, 'index.html'));
});

// �����˹�� version ��� (index-old.html)
app.get('/old', (req, res) => {
    res.setHeader('Content-Type', 'text/html; charset=utf-8');
    res.sendFile(path.join(__dirname, 'index-old.html'));
});

app.post('/scan', (req, res) => {
    const ip = req.body.ip ? req.body.ip.trim() : ''; // ź��ͧ��ҧ˹��-��ѧ
    const scanType = req.body.scanType;
    const specifiedPort = req.body.specifiedPort;

    // ��Ѻ regex ����״�����ҡ���
    const ipRegex = /^(?:(?:[0-9]{1,3}\.){3}[0-9]{1,3}(?:\/[0-9]{1,2})?)$/;
    if (!ip || !ipRegex.test(ip)) {
        res.setHeader('Content-Type', 'application/json; charset=utf-8');
        return res.status(400).json({ error: '������� IP ���� CIDR ���١��ͧ ��سҵ�Ǩ�ͺ�ٻẺ (�� 192.168.1.1 ���� 192.168.1.0/24)' });
    }

    const isCIDR = ip.includes('/');
    let command = '';

    if (scanType === 'all') {
        command = isCIDR 
            ? `${nmapPath} -p- -Pn -n -T4 --min-rate 1000 ${ip} -oA nmap-scan` // ���� --min-rate ������觡���᡹
            : `${nmapPath} -p- -Pn -n -T4 --min-rate 1000 ${ip} -oA nmap-scan`;
    } else if (scanType === 'specified') {
        command = specifiedPort 
            ? `${nmapPath} -p ${specifiedPort} -O ${ip} -oA nmap-scan` 
            : `${nmapPath} -O ${ip} -oA nmap-scan`;
    } else if (scanType === 'quick') {
        command = isCIDR 
            ? `${nmapPath} -sn -T4 --min-rate 1000 ${ip} -oA nmap-scan`
            : `${nmapPath} -n -T4 --min-rate 1000 ${ip} -oA nmap-scan`;
    }

    exec(command, { encoding: 'utf8', timeout: 600000 }, (error, stdout, stderr) => { // ���� timeout �� 600 �Թҷ�
        if (error) {
            console.error(`Error: ${error.message}`);
            console.error(`Stderr: ${stderr}`);
            res.setHeader('Content-Type', 'application/json; charset=utf-8');
            let errorMessage = '�Դ��ͼԴ��Ҵ㹡���᡹: ';
            if (error.code === 1) {
                errorMessage += '�������ö�᡹ IP ���� subnet �� �Ҩ�١���͡���������������������ʵ�����ҹ';
            } else if (error.killed && error.signal === 'SIGTERM') {
                errorMessage += '����᡹�����ҹҹ�Թ� (timeout)';
            } else {
                errorMessage += error.message;
            }
            return res.status(500).json({ error: errorMessage, details: stderr });
        }
        if (stderr) {
            console.error(`Nmap stderr: ${stderr}`);
        }

        const scanResults = parseNmapOutput(stdout, ip, scanType, isCIDR);
        res.setHeader('Content-Type', 'application/json; charset=utf-8');
        res.json(scanResults);
    });
});

function parseNmapOutput(output, ip, scanType, isCIDR) {
    const lines = output.split('\n');
    let ports = [];
    let hosts = [];

    if (isCIDR) {
        let currentHost = null;
        lines.forEach(line => {
            if (line.includes('Nmap scan report for')) {
                const hostMatch = line.match(/Nmap scan report for ([\d.]+)/);
                if (hostMatch) {
                    currentHost = { ip: hostMatch[1], ports: [] };
                    hosts.push(currentHost);
                }
            } else if (line.includes('open') && currentHost) {
                const portMatch = line.match(/(\d+)\/tcp\s+open\s+(.+)/);
                if (portMatch) {
                    currentHost.ports.push({
                        number: portMatch[1],
                        service: portMatch[2] || '����Һ',
                        status: 'open'
                    });
                }
            } else if (line.includes('closed') && currentHost) {
                const portMatch = line.match(/(\d+)\/tcp\s+closed/);
                if (portMatch) {
                    currentHost.ports.push({
                        number: portMatch[1],
                        service: '����Һ',
                        status: 'closed'
                    });
                }
            }
        });

        return {
            ip: ip,
            timestamp: new Date().toISOString(),
            scanType: scanType,
            hosts: hosts.length > 0 ? hosts : []
        };
    } else {
        lines.forEach(line => {
            if (line.includes('open')) {
                const portMatch = line.match(/(\d+)\/tcp\s+open\s+(.+)/);
                if (portMatch) {
                    ports.push({
                        number: portMatch[1],
                        service: portMatch[2] || '����Һ',
                        status: 'open'
                    });
                }
            } else if (line.includes('closed')) {
                const portMatch = line.match(/(\d+)\/tcp\s+closed/);
                if (portMatch) {
                    ports.push({
                        number: portMatch[1],
                        service: '����Һ',
                        status: 'closed'
                    });
                }
            }
        });

        return {
            ip: ip,
            timestamp: new Date().toISOString(),
            scanType: scanType,
            ports: ports.length > 0 ? ports : []
        };
    }
}

app.listen(port, () => {
    console.log(`Server is running on port ${port}`);
});