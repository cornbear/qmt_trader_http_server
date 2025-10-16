/**
 * QMT交易系统 - 外部交易接口测试脚本 (JavaScript版本)
 * 使用HMAC-SHA256签名验证
 */

const crypto = require('crypto');
const https = require('https');
const http = require('http');
const { URL } = require('url');

function generateSignature(method, path, queryString, body, timestamp, clientId, secretKey) {
    // 构建签名字符串
    const signString = `${method}\n${path}\n${queryString}\n${body}\n${timestamp}\n${clientId}`;
    
    // 计算HMAC-SHA256签名
    const signature = crypto
        .createHmac('sha256', secretKey)
        .update(signString)
        .digest('hex');
    
    return signature;
}

function makeRequest(url, options, data) {
    return new Promise((resolve, reject) => {
        const urlObj = new URL(url);
        const isHttps = urlObj.protocol === 'https:';
        const client = isHttps ? https : http;
        
        const requestOptions = {
            hostname: urlObj.hostname,
            port: urlObj.port || (isHttps ? 443 : 80),
            path: urlObj.pathname + urlObj.search,
            method: options.method,
            headers: options.headers,
            timeout: 30000
        };
        
        const req = client.request(requestOptions, (res) => {
            let responseData = '';
            
            res.on('data', (chunk) => {
                responseData += chunk;
            });
            
            res.on('end', () => {
                try {
                    const result = {
                        statusCode: res.statusCode,
                        data: JSON.parse(responseData)
                    };
                    resolve(result);
                } catch (e) {
                    resolve({
                        statusCode: res.statusCode,
                        data: responseData
                    });
                }
            });
        });
        
        req.on('error', (error) => {
            reject(error);
        });
        
        req.on('timeout', () => {
            req.destroy();
            reject(new Error('Request timeout'));
        });
        
        if (data) {
            req.write(JSON.stringify(data, Object.keys(data).sort()));
        }
        
        req.end();
    });
}

async function callOuterTradeApi(operation = 'buy') {
    console.log(`=== 测试单笔${operation}交易接口 ===`);
    
    // 配置信息
    const baseUrl = "http://localhost:9091";
    const clientId = "outer_client_002";
    const secretKey = "qmt_secret_key_zzzz";
    
    // 请求参数
    const method = "POST";
    const path = `/qmt/trade/api/outer/trade/${operation}`;
    const queryString = "";  // 没有查询参数
    
    // 请求体
    const data = {
        trader_index: 0,
        symbol: "000001",
        trade_price: 10.50,
        position_pct: 0.1,  // 10%仓位
        strategy_name: "外部策略测试"
    };
    const body = JSON.stringify(data, Object.keys(data).sort());
    
    // 生成时间戳
    const timestamp = Math.floor(Date.now() / 1000).toString();
    
    // 生成签名
    const signature = generateSignature(method, path, queryString, body, timestamp, clientId, secretKey);
    
    // 构建请求头
    const headers = {
        'Content-Type': 'application/json',
        'X-Client-ID': clientId,
        'X-Timestamp': timestamp,
        'X-Signature': signature
    };
    
    // 发送请求
    const url = `${baseUrl}${path}`;
    try {
        const response = await makeRequest(url, { method: 'POST', headers }, data);
        
        console.log(`状态码: ${response.statusCode}`);
        console.log(`响应:`, response.data);
        
        return response;
    } catch (error) {
        console.error('请求失败:', error.message);
        return null;
    }
}

async function callOuterTradeBatchApi(operation = 'buy') {
    console.log(`\n=== 测试批量${operation}交易接口 ===`);
    
    // 配置信息
    const baseUrl = "http://localhost:9091";
    const clientId = "outer_client_002";
    const secretKey = "qmt_secret_key_zzzz";
    
    // 请求参数
    const method = "POST";
    const path = `/qmt/trade/api/outer/trade/batch/${operation}`;
    const queryString = "";  // 没有查询参数
    
    // 请求体
    const data = {
        symbol: "000001",
        trade_price: 10.50,
        position_pct: 0.1,  // 10%仓位
        strategy_name: "外部批量策略测试"
    };
    const body = JSON.stringify(data, Object.keys(data).sort());
    
    // 生成时间戳
    const timestamp = Math.floor(Date.now() / 1000).toString();
    
    // 生成签名
    const signature = generateSignature(method, path, queryString, body, timestamp, clientId, secretKey);
    
    // 构建请求头
    const headers = {
        'Content-Type': 'application/json',
        'X-Client-ID': clientId,
        'X-Timestamp': timestamp,
        'X-Signature': signature
    };
    
    // 发送请求
    const url = `${baseUrl}${path}`;
    try {
        const response = await makeRequest(url, { method: 'POST', headers }, data);
        
        console.log(`状态码: ${response.statusCode}`);
        console.log(`响应:`, response.data);
        
        return response;
    } catch (error) {
        console.error('请求失败:', error.message);
        return null;
    }
}

async function testDifferentOperations() {
    console.log('\n=== 测试不同操作类型 ===');
    
    const operations = ['buy', 'sell'];
    
    for (const operation of operations) {
        console.log(`\n--- 测试 ${operation} 操作 ---`);
        await callOuterTradeApi(operation);
        
        console.log(`\n--- 测试批量 ${operation} 操作 ---`);
        await callOuterTradeBatchApi(operation);
        
        // 等待一秒避免请求过快
        await new Promise(resolve => setTimeout(resolve, 1000));
    }
}

async function callOuterTradeWithOrderNum(operation = 'buy', orderNum = 100) {
    console.log(`\n=== 测试按固定股数${operation}交易（order_num=${orderNum}）===`);
    
    // 配置信息
    const baseUrl = "http://localhost:9091";
    const clientId = "outer_client_002";
    const secretKey = "qmt_secret_key_zzzz";
    
    // 请求参数
    const method = "POST";
    const path = `/qmt/trade/api/outer/trade/${operation}`;
    const queryString = "";
    
    // 请求体 - 使用 order_num 而不是 position_pct
    const data = {
        trader_index: 0,
        symbol: "000001",
        trade_price: 10.50,
        order_num: orderNum,  // 直接指定委托股数
        price_type: 0,  // 0:限价单
        strategy_name: "外部策略-固定股数"
    };
    const body = JSON.stringify(data, Object.keys(data).sort());
    
    // 生成时间戳
    const timestamp = Math.floor(Date.now() / 1000).toString();
    
    // 生成签名
    const signature = generateSignature(method, path, queryString, body, timestamp, clientId, secretKey);
    
    // 构建请求头
    const headers = {
        'Content-Type': 'application/json',
        'X-Client-ID': clientId,
        'X-Timestamp': timestamp,
        'X-Signature': signature
    };
    
    // 发送请求
    const url = `${baseUrl}${path}`;
    try {
        const response = await makeRequest(url, { method: 'POST', headers }, data);
        console.log(`状态码: ${response.statusCode}`);
        console.log(`响应:`, response.data);
        return response;
    } catch (error) {
        console.error('请求失败:', error.message);
        return null;
    }
}

async function testOrderNumMode() {
    console.log('\n=== 测试按固定股数交易（order_num模式）===');
    
    console.log('\n--- 买入 100 股 ---');
    await callOuterTradeWithOrderNum('buy', 100);
    await new Promise(resolve => setTimeout(resolve, 500));
    
    console.log('\n--- 买入 500 股 ---');
    await callOuterTradeWithOrderNum('buy', 500);
    await new Promise(resolve => setTimeout(resolve, 500));
    
    console.log('\n--- 卖出 200 股 ---');
    await callOuterTradeWithOrderNum('sell', 200);
}

async function testMixedPriceTypes() {
    console.log('\n=== 测试不同价格类型 ===');
    
    const baseUrl = "http://localhost:9091";
    const clientId = "outer_client_002";
    const secretKey = "qmt_secret_key_zzzz";
    
    const priceTypes = {
        0: "限价",
        1: "最新价",
        2: "最优五档即时成交剩余撤销",
        3: "本方最优",
        5: "对方最优"
    };
    
    for (const [priceType, typeName] of Object.entries(priceTypes)) {
        console.log(`\n--- 测试价格类型: ${priceType} (${typeName}) ---`);
        
        const method = "POST";
        const path = "/qmt/trade/api/outer/trade/buy";
        const queryString = "";
        
        const data = {
            trader_index: 0,
            symbol: "000001",
            trade_price: 10.50,
            order_num: 100,
            price_type: parseInt(priceType),
            strategy_name: `测试${typeName}`
        };
        const body = JSON.stringify(data, Object.keys(data).sort());
        const timestamp = Math.floor(Date.now() / 1000).toString();
        const signature = generateSignature(method, path, queryString, body, timestamp, clientId, secretKey);
        
        const headers = {
            'Content-Type': 'application/json',
            'X-Client-ID': clientId,
            'X-Timestamp': timestamp,
            'X-Signature': signature
        };
        
        const url = `${baseUrl}${path}`;
        try {
            const response = await makeRequest(url, { method: 'POST', headers }, data);
            console.log(`状态码: ${response.statusCode}`);
            console.log(`响应:`, response.data);
        } catch (error) {
            console.error('请求失败:', error.message);
        }
        
        await new Promise(resolve => setTimeout(resolve, 500));
    }
}

async function testParameterValidation() {
    console.log('\n=== 测试参数验证 ===');
    
    const baseUrl = "http://localhost:9091";
    const clientId = "outer_client_002";
    const secretKey = "qmt_secret_key_zzzz";
    
    const testCases = [
        {
            name: "同时提供position_pct和order_num（应该失败）",
            data: {
                trader_index: 0,
                symbol: "000001",
                trade_price: 10.50,
                position_pct: 0.1,
                order_num: 100
            }
        },
        {
            name: "不提供position_pct和order_num（应该失败）",
            data: {
                trader_index: 0,
                symbol: "000001",
                trade_price: 10.50
            }
        },
        {
            name: "order_num不是100的倍数（应该失败）",
            data: {
                trader_index: 0,
                symbol: "000001",
                trade_price: 10.50,
                order_num: 150
            }
        },
        {
            name: "position_pct超出范围（应该失败）",
            data: {
                trader_index: 0,
                symbol: "000001",
                trade_price: 10.50,
                position_pct: 1.5
            }
        }
    ];
    
    for (const testCase of testCases) {
        console.log(`\n--- ${testCase.name} ---`);
        
        const method = "POST";
        const path = "/qmt/trade/api/outer/trade/buy";
        const queryString = "";
        
        const body = JSON.stringify(testCase.data, Object.keys(testCase.data).sort());
        const timestamp = Math.floor(Date.now() / 1000).toString();
        const signature = generateSignature(method, path, queryString, body, timestamp, clientId, secretKey);
        
        const headers = {
            'Content-Type': 'application/json',
            'X-Client-ID': clientId,
            'X-Timestamp': timestamp,
            'X-Signature': signature
        };
        
        const url = `${baseUrl}${path}`;
        try {
            const response = await makeRequest(url, { method: 'POST', headers }, testCase.data);
            console.log(`状态码: ${response.statusCode}`);
            console.log(`响应:`, response.data);
        } catch (error) {
            console.error('请求失败:', error.message);
        }
        
        await new Promise(resolve => setTimeout(resolve, 500));
    }
}

async function testInvalidSignature() {
    console.log('\n=== 测试无效签名 ===');
    
    // 配置信息
    const baseUrl = "http://localhost:9091";
    const clientId = "outer_client_002";
    
    // 请求参数
    const method = "POST";
    const path = "/qmt/trade/api/outer/trade/buy";
    
    // 请求体
    const data = {
        trader_index: 0,
        symbol: "000001",
        trade_price: 10.50,
        position_pct: 0.1,
        strategy_name: "无效签名测试"
    };
    
    // 生成时间戳
    const timestamp = Math.floor(Date.now() / 1000).toString();
    
    // 构建请求头（使用错误的签名）
    const headers = {
        'Content-Type': 'application/json',
        'X-Client-ID': clientId,
        'X-Timestamp': timestamp,
        'X-Signature': 'invalid_signature_for_testing'
    };
    
    // 发送请求
    const url = `${baseUrl}${path}`;
    try {
        const response = await makeRequest(url, { method: 'POST', headers }, data);
        console.log(`状态码: ${response.statusCode}`);
        console.log(`响应:`, response.data);
    } catch (error) {
        console.error('请求失败:', error.message);
    }
}

async function main() {
    console.log('QMT交易系统 - 外部交易接口测试 (JavaScript版本)');
    console.log('='.repeat(60));
    
    try {
        console.log('\n【原有功能测试 - 按仓位比例交易】');
        
        // 测试单笔买入交易接口
        console.log('\n1. 测试单笔买入交易接口（按仓位比例）');
        await callOuterTradeApi('buy');
        
        // 测试单笔卖出交易接口
        console.log('\n2. 测试单笔卖出交易接口（按仓位比例）');
        await callOuterTradeApi('sell');
        
        // 测试批量买入交易接口
        console.log('\n3. 测试批量买入交易接口（按仓位比例）');
        await callOuterTradeBatchApi('buy');
        
        // 测试批量卖出交易接口
        console.log('\n4. 测试批量卖出交易接口（按仓位比例）');
        await callOuterTradeBatchApi('sell');
        
        console.log('\n【新增功能测试 - 按固定股数交易】');
        
        // 测试按固定股数交易
        console.log('\n5. 测试按固定股数交易（order_num模式）');
        await testOrderNumMode();
        
        // 测试不同价格类型
        console.log('\n6. 测试不同价格类型');
        await testMixedPriceTypes();
        
        console.log('\n【参数验证测试】');
        
        // 测试参数验证
        console.log('\n7. 测试参数验证');
        await testParameterValidation();
        
        console.log('\n【安全测试】');
        
        // 测试无效签名
        console.log('\n8. 测试无效签名');
        await testInvalidSignature();
        
        console.log('\n\n=== 测试完成 ===');
    } catch (error) {
        console.error('测试过程中发生错误:', error);
    }
}

if (require.main === module) {
    main();
}

module.exports = {
    generateSignature,
    callOuterTradeApi,
    callOuterTradeBatchApi,
    callOuterTradeWithOrderNum,
    testDifferentOperations,
    testOrderNumMode,
    testMixedPriceTypes,
    testParameterValidation,
    testInvalidSignature
};