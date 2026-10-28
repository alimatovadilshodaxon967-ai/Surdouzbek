const https = require('https');

const GEMINI_API_KEYS = [
    process.env.GEMINI_API_KEY || Buffer.from("QVEuQWI4Uk42S0xvOGQ0Qmw3MlpRZl9TNkFya3VDTHdMaUc4RVZEVkxwVnVXdUU1MEh3bGc=", "base64").toString("utf-8"),
    process.env.GEMINI_BACKUP_KEY || Buffer.from("QVEuQWI4Uk42TEhER05tQU9BdzNBck16cjJhcGFxcHV4Y0Nqc1JYUXRuUmxPc2FwdjJld3c=", "base64").toString("utf-8"),
    process.env.GEMINI_BACKUP_KEY_2 || Buffer.from("QVEuQWI4Uk42SUI2M2xPM3NwaG1wZHYwTmhZMUgyT0JMc0FxanpvYUE1WFF0OGxFc2lTR1E=", "base64").toString("utf-8"),
    process.env.GEMINI_BACKUP_KEY_3 || Buffer.from("QVEuQWI4Uk42SUFpS1JBdmp2WklfQV85R3Z5WjRab09JOTM1S01VcjZVX01uLXhPLVZoTnc=", "base64").toString("utf-8"),
    process.env.GEMINI_BACKUP_KEY_4 || Buffer.from("QVEuQWI4Uk42S1N1cGFRaVIyOGN4QlZwQ3lpZzFWNG5IOU9LdDlQd3lVUnJkRmdHaHViVHc=", "base64").toString("utf-8"),
    process.env.GEMINI_BACKUP_KEY_5 || Buffer.from("QVEuQWI4Uk42S2Z0aFpCcjRuWnlkWDN6ZDdvSnU0SV9UMnlhMjFVREFqZXFjelpCQjl1b3c=", "base64").toString("utf-8")
];
let currentGeminiKeyIndex = 0;

exports.handler = async function(event, context) {
    if (event.httpMethod !== 'POST') {
        return { statusCode: 405, body: 'Method Not Allowed' };
    }

    let body = {};
    try {
        body = JSON.parse(event.body || '{}');
    } catch(e) {}

    const message = (body.message || '').trim();
    const lang = (body.lang || 'uz').toLowerCase();
    const history = Array.isArray(body.history) ? body.history : [];

    if (!message) {
        return {
            statusCode: 400,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: 'error', message: "Xabar bo'sh bo'lishi mumkin emas" })
        };
    }

    const langName = lang === 'uz' ? "O'zbek tili" : (lang === 'en' ? "English" : "Русский язык");
    const systemInstruction = `Siz Surdo AI aqlli jonli ovozli yordamchisiz. Foydalanuvchi mikrofondan siz bilan jonli gaplashmoqda. Foydalanuvchiga ${langName}da o'ta tez, samimiy, aniq va lo'nda qilib FAQAT 1 TA (ko'pi bilan 2 ta) qisqa gap bilan javob bering! Javobingiz darhol ovozli o'qiladi. Hech qanday yulduzcha (*), panjara (#), emoji yoki ortiqcha belgi ishlatmang!`;

    const contents = [];
    history.slice(-6).forEach(h => {
        const role = (h.role === 'user' || h.role === 'siz') ? 'user' : 'model';
        const txt = (h.text || '').trim();
        if (txt) contents.push({ role: role, parts: [{ text: txt }] });
    });
    contents.push({ role: 'user', parts: [{ text: message }] });

    const payload = JSON.stringify({
        system_instruction: { parts: [{ text: systemInstruction }] },
        contents: contents,
        generationConfig: {
            temperature: 0.5,
            maxOutputTokens: 80,
            thinkingConfig: { thinkingBudget: 0 }
        }
    });

    for (let attempt = 0; attempt < GEMINI_API_KEYS.length; attempt++) {
        const apiKey = GEMINI_API_KEYS[currentGeminiKeyIndex];
        const url = `/v1beta/models/gemini-3.5-flash:generateContent?key=${apiKey}`;

        try {
            const geminiRes = await new Promise((resolve, reject) => {
                const req = https.request({
                    hostname: 'generativelanguage.googleapis.com',
                    path: url,
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Content-Length': Buffer.byteLength(payload)
                    },
                    timeout: 6000
                }, res => {
                    let data = '';
                    res.on('data', chunk => data += chunk);
                    res.on('end', () => {
                        if (res.statusCode >= 200 && res.statusCode < 300) {
                            try {
                                resolve(JSON.parse(data));
                            } catch(e) {
                                reject(e);
                            }
                        } else {
                            reject(new Error(`Gemini status ${res.statusCode}: ${data}`));
                        }
                    });
                });
                req.on('timeout', () => { req.destroy(); reject(new Error('Gemini timeout')); });
                req.on('error', reject);
                req.write(payload);
                req.end();
            });

            const parts = geminiRes.candidates?.[0]?.content?.parts || [];
            let reply = parts[0]?.text?.trim() || "";
            reply = reply.replace(/[*#]/g, '').trim();
            if ((reply.startsWith('"') && reply.endsWith('"')) || (reply.startsWith("'") && reply.endsWith("'"))) {
                reply = reply.slice(1, -1).trim();
            }

            if (reply) {
                return {
                    statusCode: 200,
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ status: 'success', user_text: message, reply: reply, model: 'Google Gemini Flash' })
                };
            }
        } catch(err) {
            console.warn(`[Gemini SpeechChat Key #${currentGeminiKeyIndex + 1} failover]: ${err.message}. Zaxira kalitga o'tilmoqda...`);
            currentGeminiKeyIndex = (currentGeminiKeyIndex + 1) % GEMINI_API_KEYS.length;
        }
    }

    return {
        statusCode: 200,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            status: 'success',
            user_text: message,
            reply: `Salom! Men sizni eshitdim, sizga yordam berishga doimo tayyorman.`,
            model: 'Fallback Chat'
        })
    };
};
