const express = require('express');
const { exec } = require('child_process');
const bodyParser = require('body-parser');
const ip = require('ip'); // ใช้ lib ip ไม่ใช้ ip-cidr

const app = express();
const port = 36969;

const nmapPath = `"C:\\Program Files (x86)\\Nmap\\nmap.exe"`; // Path ไป Nmap.exe

app.use(bodyParser.urlencoded({ extended: true }));
app.use(express.static(__dirname));

// หน้าแรก
app.get('/', (req, res) => {
  res.sendFile(__dirname + '/index.html');
});

// ฟังก์ชันแตก CIDR เป็น Array IP
function expandCIDR(cidrBlock) {
  try {
    const range = ip.cidrSubnet(cidrBlock);
    if (!range || !range.firstAddress || !range.lastAddress) {
      return [];
    }

    const ips = [];
    let current = ip.toLong(range.firstAddress);
    const last = ip.toLong(range.lastAddress);

    while (current <= last) {
      ips.push(ip.fromLong(current));
      current++;
    }

    return ips;
  } catch (e) {
    console.error("Error expanding CIDR:", e);
    return [];
  }
}

// ฟังก์ชัน Parse ผลลัพธ์จาก nmap
function parseNmapOutput(rawOutput) {
  const lines = rawOutput.split('\n');
  const results = [];
  let currentIP = '';
  let foundPort = false;

  for (const line of lines) {
    if (line.includes('Nmap scan report for')) {
      if (currentIP && !foundPort) {
        results.push({
          ip: currentIP,
          port: '-',
          state: 'No open ports or Host unreachable',
          service: '-'
        });
      }
      const match = line.match(/Nmap scan report for ([\d.]+)/);
      if (match) {
        currentIP = match[1];
        foundPort = false;
      }
    } else if (line.match(/(\d+)\/tcp\s+(open|closed|filtered)\s+(\S+)/)) {
      const portMatch = line.match(/(\d+)\/tcp\s+(open|closed|filtered)\s+(\S+)/);
      if (portMatch) {
        results.push({
          ip: currentIP,
          port: portMatch[1],
          state: portMatch[2],
          service: portMatch[3]
        });
        foundPort = true;
      }
    }
  }

  if (currentIP && !foundPort) {
    results.push({
      ip: currentIP,
      port: '-',
      state: 'No open ports or Host unreachable',
      service: '-'
    });
  }

  return results;
}

// POST /scan ยิงแต่ละ IP
app.post('/scan', async (req, res) => {
  const ipInput = req.body.ip.trim();
  const scanType = req.body.scanType;
  const specifiedPort = req.body.specifiedPort;

  let ipList = [];

  if (ipInput.includes('/')) {
    ipList = expandCIDR(ipInput);
  } else {
    ipList.push(ipInput);
  }

  const scanPromises = ipList.map(targetIP => {
    return new Promise((resolve) => {
      let command = '';

      if (scanType === 'all') {
        command = `${nmapPath} -p- -Pn -n -T4 --min-rate 5000 --max-retries 1 --initial-rtt-timeout 100ms --max-rtt-timeout 300ms --host-timeout 2m ${targetIP}`;
      } else if (scanType === 'specified') {
        command = specifiedPort 
          ? `${nmapPath} -p ${specifiedPort} -Pn -n -T4 ${targetIP}`
          : `${nmapPath} -O ${targetIP}`;
      } else if (scanType === 'quick') {
        command = `${nmapPath} -sn -T4 ${targetIP}`;
      }

      console.log(`Running: ${command}`);

      exec(command, { encoding: 'utf8', timeout: 60000 }, (error, stdout, stderr) => {
        if (error) {
          console.error(`Scan error for ${targetIP}: ${error.message}`);
          return resolve([]);
        }
        const parsed = parseNmapOutput(stdout);
        resolve(parsed);
      });
    });
  });

  const allResults = await Promise.all(scanPromises);
  const flattenedResults = allResults.flat();

  res.setHeader('Content-Type', 'application/json; charset=utf-8');
  res.json({
    message: 'สแกนเสร็จแล้ว',
    results: flattenedResults
  });
});

app.listen(port, () => {
  console.log(`?? Server running at http://localhost:${port}`);
});
