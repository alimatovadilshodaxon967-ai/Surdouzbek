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

module.exports = async function handler(req, res) {
    if (req.method !== 'POST') {
        return res.status(405).send('Method Not Allowed');
    }

    const body = req.body || {};
    const message = (body.message || '').trim();
    const lang = (body.lang || 'uz').toLowerCase();
    const history = Array.isArray(body.history) ? body.history : [];

    if (!message) {
        return res.status(400).json({ status: 'error', message: "Xabar bo'sh bo'lishi mumkin emas" });
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
        try {
            const reply = await new Promise((resolve, reject) => {
                const r = https.request({
                    hostname: 'generativelanguage.googleapis.com',
                    path: `/v1beta/models/gemini-3.5-flash:generateContent?key=${apiKey}`,
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Content-Length': Buffer.byteLength(payload)
                    },
                    timeout: 5000
                }, (resp) => {
                    const chunks = [];
                    resp.on('data', chunk => chunks.push(chunk));
                    resp.on('end', () => {
                        if (resp.statusCode === 200) {
                            try {
                                const parsed = JSON.parse(Buffer.concat(chunks).toString());
                                const text = parsed.candidates?.[0]?.content?.parts?.[0]?.text?.trim() || '';
                                resolve(text.replace(/[*#]/g, '').trim());
                            } catch (e) {
                                reject(e);
                            }
                        } else {
                            reject(new Error(`Gemini status ${resp.statusCode}`));
                        }
                    });
                });
                r.on('timeout', () => { r.destroy(); reject(new Error('Timeout')); });
                r.on('error', reject);
                r.write(payload);
                r.end();
            });

            if (reply) {
                return res.status(200).json({ status: 'success', user_text: message, reply: reply });
            }
        } catch (err) {
            currentGeminiKeyIndex = (currentGeminiKeyIndex + 1) % GEMINI_API_KEYS.length;
            continue;
        }
    }

    return res.status(200).json({ status: 'success', user_text: message, reply: "Sizni tushundim, suhbatni davom ettiramiz." });
};
