const express = require('express');
const { exec } = require('child_process');
const bodyParser = require('body-parser');

const app = express();
const port = 36969;

// ��˹� path Ẻ����ͧ nmap.exe ���Դ�������
const nmapPath = `"C:\\Program Files (x86)\\Nmap\\nmap.exe"`; // ����¹��� path ��ԧ�ͧ����ͧ�س

app.use(bodyParser.urlencoded({ extended: true }));
app.use(express.static(__dirname)); // ��ԡ����� static �� index.html

app.get('/', (req, res) => {
    res.sendFile(__dirname + '/index.html');
});

app.post('/scan', (req, res) => {
    const ip = req.body.ip;
    const scanType = req.body.scanType;
    const specifiedPort = req.body.specifiedPort;

    if (!ip || !/^(?:\d{1,3}\.){3}\d{1,3}$/.test(ip)) {
        return res.status(400).json({ error: '������� IP ���١��ͧ' });
    }

    let command = '';

    if (scanType === 'all') {
        command = `${nmapPath} -p- -Pn -n -T4 ${ip} -oA nmap-scan`;
    } else if (scanType === 'specified') {
        command = specifiedPort ? `${nmapPath} -p ${specifiedPort} -O ${ip} -oA nmap-scan` : `${nmapPath} -O ${ip} -oA nmap-scan`;
    } else if (scanType === 'quick') {
        command = `${nmapPath} -n -T4 ${ip} -oA nmap-scan`;
    }

    exec(command, (error, stdout, stderr) => {
        if (error) {
            return res.status(500).json({ error: `Error: ${error.message}` });
        }

        const scanResults = parseNmapOutput(stdout, ip, scanType);
        res.json(scanResults);
    });
});

function parseNmapOutput(output, ip, scanType) {
    const lines = output.split('\n');
    let ports = [];
    let currentPort = null;

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
        ports: ports.length > 0 ? ports : [{ number: 'N/A', service: '��辺����', status: 'closed' }]
    };
}

app.listen(port, () => {
    console.log(`Server is running on port ${port}`);
});