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

function pcmToWav(pcmBuffer, sampleRate = 24000, numChannels = 1, bitsPerSample = 16) {
    const header = Buffer.alloc(44);
    const byteRate = sampleRate * numChannels * (bitsPerSample / 8);
    const blockAlign = numChannels * (bitsPerSample / 8);
    const dataSize = pcmBuffer.length;
    
    header.write('RIFF', 0);
    header.writeUInt32LE(36 + dataSize, 4);
    header.write('WAVE', 8);
    header.write('fmt ', 12);
    header.writeUInt32LE(16, 16);
    header.writeUInt16LE(1, 20);
    header.writeUInt16LE(numChannels, 22);
    header.writeUInt32LE(sampleRate, 24);
    header.writeUInt32LE(byteRate, 28);
    header.writeUInt16LE(blockAlign, 32);
    header.writeUInt16LE(bitsPerSample, 34);
    header.write('data', 36);
    header.writeUInt32LE(dataSize, 40);
    
    return Buffer.concat([header, pcmBuffer]);
}

const VOICELAB_API_KEYS = [
    "vlk_jymjsVHzrXt8jTp1WtrtvH3ps1ICwZ81lLUIH81Eboc",
    "vlk_YVdii2PwwrYLGDS1bXJ4xbdEG0Qs6RnaIZZcJVIRbMg",
    "vlk_qQ4O4WlnQ-cPw23_PiBkZ8NK1Tj8Ywmu-GeltcH6VqQ",
    "vlk_WkCzoxnsKdJ3ffT3Gt-abjO9YNeyLtGY1TZlCS1VhYg",
    "vlk_sS-lIYDMWPqIaO8_iegg9D1n9SePqvNy0q6vthHk4YM",
    "vlk_Syrv5hJm2hEgsUxLNQ3cKhhmxClgFMICUduHf0EZgcc",
    "vlk_-Xishu-yP9pksI8QS_EXV8G6vJNu7VTI3Jr9NGy1s6k",
    "vlk_Vb_xPvvMYRgNW8T0r08jL1wj_JWyKOjVg5nVv852Ppw",
    "vlk_3JUy_pjdKLCP2gXDgQd-pPfnbbBjbRHpA8qQhRMoL38",
    "vlk_x7y5QaqzTurjgFKNHJ5nFAK9D8One9XaJJV7x9FGdu4"
];
let currentKeyIndex = 0;
const VOICELAB_VOICES = {
    "abdulhay": "voice_M-p5iz9z_kPWNm_C0cFqbC6X",
    "madina": "voice_4ef06e6b-2229-4023-ad66-c2a7a2b736ff",
    "amir": "voice_8bae02c6-d078-4757-9d62-0fce6da23cf7",
    "javohir": "voice_fa56cecf-9b0b-45ba-9ec3-494efb5b301f",
    "kamola": "voice_47260d60-5635-4fb0-904d-0f3c19c04ce6",
    "dilnoza": "voice_f7179d1c-07ab-4b3d-b5be-84dcf2935388",
    "jasur": "voice_ba303813-3023-48aa-a454-4b5705669d35",
    "safiya": "voice_2785aabd-21b5-4cc7-9845-2230186ef7d9",
    "shohruxmirzo": "voice_jABVrmH-0x6pbYefNCuYfH6H",
    "nozima": "voice_3602ec76-5393-43b6-9e0d-784328cb77ba",
    "sardor": "voice_xdQMoRJkjHbPIB-jounXzKq8",
    "botir": "voice_5e592ada-eca8-42e3-98fa-469c1c8fc999",
    "gulya": "voice_7b350d91-4e56-4bc3-869c-8cd6ba646c3c",
    "rustam": "voice_be56058a-8f15-48bb-904b-4fe92531d5b1"
};

exports.handler = async function(event, context) {
    const params = event.queryStringParameters || {};
    const text = (params.text || '').trim();
    const voice = (params.voice || 'madina').toLowerCase();

    if (!text) {
        return { statusCode: 400, body: 'Text query parameter is required' };
    }

    // 1. Google Gemini AI Ovoz sintezi
    if (voice.includes('gemini') || voice.includes('google')) {
        const vname = (voice.includes('puck') || voice.includes('erkak')) ? 'Puck' : 'Aoede';
        const geminiPayload = JSON.stringify({
            contents: [{ parts: [{ text: `Read aloud: ${text}` }] }],
            generationConfig: {
                responseModalities: ["AUDIO"],
                speechConfig: {
                    voiceConfig: {
                        prebuiltVoiceConfig: {
                            voiceName: vname
                        }
                    }
                }
            }
        });

        // 1 ta tezkor urinish (3.5s timeout)
        for (let attempt = 0; attempt < 1; attempt++) {
            const apiKey = GEMINI_API_KEYS[currentGeminiKeyIndex];
            try {
                const geminiBuffer = await new Promise((resolve, reject) => {
                    const req = https.request({
                        hostname: 'generativelanguage.googleapis.com',
                        path: `/v1beta/models/gemini-2.5-flash-preview-tts:generateContent?key=${apiKey}`,
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'Content-Length': Buffer.byteLength(geminiPayload)
                        },
                        timeout: 3800
                    }, (res) => {
                        const chunks = [];
                        res.on('data', chunk => chunks.push(chunk));
                        res.on('end', () => {
                            if (res.statusCode >= 200 && res.statusCode < 300) {
                                try {
                                    const parsed = JSON.parse(Buffer.concat(chunks).toString());
                                    const b64 = parsed.candidates?.[0]?.content?.parts?.[0]?.inlineData?.data;
                                    if (b64) {
                                        const pcm = Buffer.from(b64, 'base64');
                                        resolve(pcmToWav(pcm));
                                    } else {
                                        reject(new Error("Gemini audio data missing"));
                                    }
                                } catch (e) {
                                    reject(e);
                                }
                            } else {
                                reject(new Error(`Gemini status ${res.statusCode}: ${Buffer.concat(chunks).toString()}`));
                            }
                        });
                    });
                    req.on('timeout', () => { req.destroy(); reject(new Error('Gemini TTS timeout')); });
                    req.on('error', reject);
                    req.write(geminiPayload);
                    req.end();
                });

                return {
                    statusCode: 200,
                    headers: {
                        'Content-Type': 'audio/wav',
                        'Cache-Control': 'public, max-age=86400'
                    },
                    body: geminiBuffer.toString('base64'),
                    isBase64Encoded: true
                };
            } catch (geminiErr) {
                console.warn(`[Gemini Purge]: Kalit (${apiKey.substring(0, 10)}...) kvotasi tugadi. Ro'yxatdan BUTUNLAY O'CHIRILDI!`);
                const idx = GEMINI_API_KEYS.indexOf(apiKey);
                if (idx !== -1) GEMINI_API_KEYS.splice(idx, 1);
                break;
            }
        }
    }

    const voiceId = VOICELAB_VOICES[voice] || VOICELAB_VOICES["abdulhay"];
    const payload = JSON.stringify({
        text: text,
        voice_id: voiceId,
        language: "uz"
    });

    const totalKeys = VOICELAB_API_KEYS.length;
    let lastError = null;

    for (let attempt = 0; attempt < totalKeys; attempt++) {
        const apiKey = VOICELAB_API_KEYS[currentKeyIndex];
        try {
            const audioBuffer = await new Promise((resolve, reject) => {
                const req = https.request({
                    hostname: 'api.voicelab.uz',
                    path: '/v1/tts',
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${apiKey}`,
                        'Content-Type': 'application/json',
                        'Content-Length': Buffer.byteLength(payload)
                    },
                    timeout: 4000
                }, (res) => {
                    const chunks = [];
                    res.on('data', chunk => chunks.push(chunk));
                    res.on('end', () => {
                        if (res.statusCode === 200) {
                            resolve(Buffer.concat(chunks));
                        } else {
                            const errBody = Buffer.concat(chunks).toString();
                            const err = new Error(`VoiceLab API status ${res.statusCode}: ${errBody}`);
                            err.statusCode = res.statusCode;
                            reject(err);
                        }
                    });
                });
                req.on('timeout', () => { req.destroy(); reject(new Error('VoiceLab timeout')); });
                req.on('error', reject);
                req.write(payload);
                req.end();
            });

            return {
                statusCode: 200,
                headers: {
                    'Content-Type': 'audio/wav',
                    'Cache-Control': 'public, max-age=86400'
                },
                body: audioBuffer.toString('base64'),
                isBase64Encoded: true
            };
        } catch (err) {
            lastError = err;
            console.warn(`[VoiceLab Purge] Kalit (${apiKey.substring(0, 10)}...) tugadi. Ro'yxatdan BUTUNLAY O'CHIRILDI!`);
            const idx = VOICELAB_API_KEYS.indexOf(apiKey);
            if (idx !== -1) VOICELAB_API_KEYS.splice(idx, 1);
            continue;
        }
    }

    return {
        statusCode: 502,
        body: JSON.stringify({ error: 'TTS service failed', details: lastError ? lastError.message : 'Unknown' })
    };
};
