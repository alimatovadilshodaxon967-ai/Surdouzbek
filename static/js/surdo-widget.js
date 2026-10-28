/**
 * Surdo AI — O'zbekiston Imo-ishora Tili Raqamli Vidjeti (Web Widget SDK)
 * Istalgan veb-saytga 1 qator kod bilan ulanadi:
 * <script src="http://127.0.0.1:8000/static/js/surdo-widget.js" defer></script>
 */

(function () {
    if (window.__SURDO_AI_WIDGET_LOADED__) return;
    window.__SURDO_AI_WIDGET_LOADED__ = true;

    // Skript yuklangan domen/hostni aniqlash
    let scriptHost = '';
    const currentScript = document.currentScript || Array.from(document.querySelectorAll('script')).find(s => s.src && s.src.includes('surdo-widget.js'));
    if (currentScript && currentScript.src) {
        try {
            const url = new URL(currentScript.src);
            scriptHost = url.origin;
        } catch (e) {
            scriptHost = '';
        }
    }

    const BASE_URL = scriptHost;

    // Asosiy imo-ishora so'zlari lug'ati
    const WIDGET_SIGN_DICT = {
        "salom": { video: `${BASE_URL}/static/signs/words/Salom.mp4`, label: "Salom" },
        "rahmat": { video: `${BASE_URL}/static/signs/words/Rahmat.mp4`, label: "Rahmat" },
        "zor": { video: `${BASE_URL}/static/signs/words/Zor.mp4`, label: "Zo'r" },
        "kuting": { video: `${BASE_URL}/static/signs/words/Kuting.mp4`, label: "Kuting" },
        "sevaman": { video: `${BASE_URL}/static/signs/words/Sevaman.mp4`, label: "Sevaman" },
        "yoq": { video: `${BASE_URL}/static/signs/words/Yoq.mp4`, label: "Yo'q" },
        "ha": { video: `${BASE_URL}/static/signs/words/Ha.mp4`, label: "Ha" },
        "yordam": { video: `${BASE_URL}/static/signs/words/Help.mp4`, label: "Yordam" },
        "ozbekiston": { video: `${BASE_URL}/static/signs/words/World.mp4`, label: "O'zbekiston" },
        "respublika": { video: `${BASE_URL}/static/signs/words/World.mp4`, label: "Respublika" },
        "ijtimoiy": { video: `${BASE_URL}/static/signs/words/Group.mp4`, label: "Ijtimoiy" },
        "xizmat": { video: `${BASE_URL}/static/signs/words/Work.mp4`, label: "Xizmat" },
        "aholi": { video: `${BASE_URL}/static/signs/words/People.mp4`, label: "Aholi" },
        "davlat": { video: `${BASE_URL}/static/signs/words/World.mp4`, label: "Davlat" },
        "inson": { video: `${BASE_URL}/static/signs/words/People.mp4`, label: "Inson" },
        "bola": { video: `${BASE_URL}/static/signs/words/Children.mp4`, label: "Bola" },
        "oila": { video: `${BASE_URL}/static/signs/words/Family.mp4`, label: "Oila" },
        "uy": { video: `${BASE_URL}/static/signs/words/Home.mp4`, label: "Uy" },
        "til": { video: `${BASE_URL}/static/signs/words/Language.mp4`, label: "Til" },
        "surdo": { video: `${BASE_URL}/static/signs/words/Sign.mp4`, label: "Surdo" }
    };

    // Kirill -> Lotin transliteratsiya jadvali
    const CYR_TO_LAT = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo', 'ж': 'j', 'з': 'z',
        'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r',
        'с': 's', 'т': 't', 'у': 'u', 'ф': 'f', 'х': 'x', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sh',
        'ъ': '', 'ы': 'i', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya', 'ў': 'o', 'қ': 'q', 'ғ': 'g', 'ҳ': 'h'
    };

    function cyrillicToLatin(text) {
        return text.split('').map(c => {
            const low = c.toLowerCase();
            return CYR_TO_LAT[low] !== undefined ? CYR_TO_LAT[low] : c;
        }).join('');
    }

    // CSS Uslublarini sahifaga ineksiya qilish
    const style = document.createElement('style');
    style.id = 'surdo-ai-widget-styles';
    style.textContent = `
        /* Surdo AI Vidjet Asosiy Uslublari */
        .surdo-w-fab {
            position: fixed;
            bottom: 24px;
            right: 24px;
            z-index: 999999;
            width: 58px;
            height: 58px;
            border-radius: 50%;
            background: linear-gradient(135deg, #00f2fe 0%, #4facfe 100%);
            box-shadow: 0 8px 24px rgba(0, 242, 254, 0.4), 0 4px 12px rgba(0, 0, 0, 0.3);
            border: 2px solid #ffffff;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            user-select: none;
        }
        .surdo-w-fab:hover {
            transform: scale(1.08);
            box-shadow: 0 12px 30px rgba(0, 242, 254, 0.6), 0 6px 16px rgba(0, 0, 0, 0.4);
        }
        .surdo-w-fab-icon {
            font-size: 26px;
        }

        /* Qalqib chiquvchi Oyna (Modal Card) */
        .surdo-w-modal {
            position: fixed;
            bottom: 92px;
            right: 24px;
            z-index: 999999;
            width: 330px;
            height: 480px;
            background: #0a0f1d;
            border: 1.5px solid rgba(0, 242, 254, 0.35);
            border-radius: 20px;
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.8), 0 0 30px rgba(0, 242, 254, 0.25);
            display: none;
            flex-direction: column;
            overflow: hidden;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            color: #ffffff;
            backdrop-filter: blur(20px);
            transition: all 0.3s ease;
        }
        .surdo-w-modal.open {
            display: flex;
            animation: surdoWPopIn 0.3s cubic-bezier(0.16, 1, 0.3, 1);
        }
        .surdo-w-modal.expanded {
            width: 420px;
            height: 590px;
        }
        @keyframes surdoWPopIn {
            0% { opacity: 0; transform: translateY(20px) scale(0.95); }
            100% { opacity: 1; transform: translateY(0) scale(1); }
        }

        /* Header (Yuqori boshqaruv paneli) */
        .surdo-w-header {
            padding: 10px 14px;
            background: rgba(14, 22, 40, 0.95);
            border-bottom: 1px solid rgba(255, 255, 255, 0.08);
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        .surdo-w-header-top {
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .surdo-w-title {
            font-size: 14px;
            font-weight: 700;
            color: #00f2fe;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .surdo-w-title-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #10b981;
            box-shadow: 0 0 8px #10b981;
            animation: surdoWPulse 2s infinite;
        }
        @keyframes surdoWPulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.5; transform: scale(0.85); }
        }
        .surdo-w-actions {
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .surdo-w-btn {
            background: rgba(255, 255, 255, 0.08);
            border: 1px solid rgba(255, 255, 255, 0.12);
            color: #cbd5e1;
            width: 26px;
            height: 26px;
            border-radius: 6px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 13px;
            transition: all 0.2s;
        }
        .surdo-w-btn:hover {
            background: rgba(0, 242, 254, 0.2);
            color: #ffffff;
            border-color: #00f2fe;
        }

        /* Tillar va Tezlik tugmalari (Rasm uslubida) */
        .surdo-w-toolbar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: rgba(0, 0, 0, 0.35);
            padding: 4px 6px;
            border-radius: 8px;
        }
        .surdo-w-pills {
            display: flex;
            align-items: center;
            gap: 4px;
        }
        .surdo-w-pill {
            background: transparent;
            border: none;
            color: #94a3b8;
            padding: 2px 7px;
            font-size: 11px;
            font-weight: 600;
            border-radius: 5px;
            cursor: pointer;
            transition: all 0.2s;
        }
        .surdo-w-pill.active {
            background: #2563eb;
            color: #ffffff;
        }
        .surdo-w-badge {
            font-size: 10px;
            font-weight: 600;
            color: #38bdf8;
            background: rgba(56, 189, 248, 0.12);
            border: 1px solid rgba(56, 189, 248, 0.3);
            border-radius: 6px;
            padding: 2px 7px;
        }

        /* Avatar Video Viewport */
        .surdo-w-viewport {
            flex: 1;
            position: relative;
            background: #050b14;
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
        }
        .surdo-w-video {
            width: 100%;
            height: 100%;
            object-fit: cover;
            display: block;
        }
        .surdo-w-caption {
            position: absolute;
            bottom: 10px;
            left: 10px;
            right: 10px;
            background: rgba(10, 15, 29, 0.88);
            border: 1px solid rgba(0, 242, 254, 0.4);
            border-radius: 10px;
            padding: 6px 10px;
            font-size: 12px;
            font-weight: 600;
            color: #ffffff;
            backdrop-filter: blur(8px);
            text-align: center;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.6);
        }

        /* Pastki boshqaruv & Matn kiritish paneli */
        .surdo-w-footer {
            padding: 10px;
            background: rgba(14, 22, 40, 0.95);
            border-top: 1px solid rgba(255, 255, 255, 0.08);
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        .surdo-w-input-wrap {
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .surdo-w-input {
            flex: 1;
            background: rgba(255, 255, 255, 0.06);
            border: 1px solid rgba(255, 255, 255, 0.15);
            border-radius: 8px;
            padding: 6px 10px;
            font-size: 12px;
            color: #ffffff;
            outline: none;
            transition: all 0.2s;
        }
        .surdo-w-input:focus {
            border-color: #00f2fe;
            background: rgba(255, 255, 255, 0.1);
        }
        .surdo-w-submit-btn {
            background: #00f2fe;
            color: #050b14;
            border: none;
            border-radius: 8px;
            padding: 6px 10px;
            font-size: 11px;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.2s;
        }
        .surdo-w-submit-btn:hover {
            background: #38bdf8;
        }
        .surdo-w-mic-btn {
            background: rgba(255, 255, 255, 0.08);
            border: 1px solid rgba(255, 255, 255, 0.15);
            color: #38bdf8;
            border-radius: 8px;
            padding: 6px 9px;
            font-size: 12px;
            cursor: pointer;
        }
        .surdo-w-mic-btn.listening {
            background: #ef4444;
            color: #ffffff;
            animation: surdoWPulse 1s infinite;
        }
        .surdo-w-chips {
            display: flex;
            align-items: center;
            gap: 4px;
            overflow-x: auto;
            padding-bottom: 2px;
        }
        .surdo-w-chip {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            color: #cbd5e1;
            border-radius: 6px;
            padding: 2px 7px;
            font-size: 10px;
            cursor: pointer;
            white-space: nowrap;
            transition: all 0.15s;
        }
        .surdo-w-chip:hover {
            border-color: #00f2fe;
            color: #00f2fe;
            background: rgba(0, 242, 254, 0.1);
        }

        /* Matn tanlanganda chiquvchi qulay tugmacha (Chrome Extension uslubi) */
        .surdo-w-selection-tooltip {
            position: absolute;
            z-index: 999998;
            background: #0a0f1d;
            border: 1.5px solid #00f2fe;
            border-radius: 8px;
            padding: 4px 8px;
            box-shadow: 0 8px 20px rgba(0, 0, 0, 0.6), 0 0 15px rgba(0, 242, 254, 0.4);
            color: #ffffff;
            font-size: 11px;
            font-weight: 600;
            cursor: pointer;
            display: none;
            align-items: center;
            gap: 5px;
            user-select: none;
            animation: surdoWPopIn 0.2s ease;
        }
        .surdo-w-selection-tooltip:hover {
            background: #00f2fe;
            color: #050b14;
        }
    `;
    document.head.appendChild(style);

    // Vidjet HTML strukturasini yaratish
    const widgetContainer = document.createElement('div');
    widgetContainer.id = 'surdo-ai-widget-root';
    widgetContainer.innerHTML = `
        <!-- Floating FAB Button -->
        <div id="surdo-w-fab" class="surdo-w-fab" title="Surdo AI — Imo-ishora Tarjimoni">
            <span class="surdo-w-fab-icon">🤟</span>
        </div>

        <!-- Floating Modal (Rasm uslubida) -->
        <div id="surdo-w-modal" class="surdo-w-modal">
            <div class="surdo-w-header">
                <div class="surdo-w-header-top">
                    <div class="surdo-w-title">
                        <span class="surdo-w-title-dot"></span>
                        Surdo AI
                    </div>
                    <div class="surdo-w-actions">
                        <button id="surdo-w-expand-btn" class="surdo-w-btn" title="Kattalashtirish / Kichraytirish">⤢</button>
                        <button id="surdo-w-close-btn" class="surdo-w-btn" title="Yopish">✕</button>
                    </div>
                </div>
                <div class="surdo-w-toolbar">
                    <div class="surdo-w-pills">
                        <button class="surdo-w-pill active" data-lang="uz">uz</button>
                        <button class="surdo-w-pill" data-lang="cyr">ўз</button>
                        <button class="surdo-w-pill" data-lang="ru">ru</button>
                        <button id="surdo-w-speed-btn" class="surdo-w-pill">1x</button>
                    </div>
                    <div id="surdo-w-status" class="surdo-w-badge">Tayyor...</div>
                </div>
            </div>

            <div class="surdo-w-viewport">
                <video id="surdo-w-video" class="surdo-w-video" playsinline autoplay muted loop src="${BASE_URL}/static/avatars/real_human_presenter.mp4"></video>
                <div id="surdo-w-caption" class="surdo-w-caption">Imo-ishora kutilmoqda...</div>
            </div>

            <div class="surdo-w-footer">
                <div class="surdo-w-input-wrap">
                    <input type="text" id="surdo-w-input" class="surdo-w-input" placeholder="Matn yozing yoki so'z tanlang..." />
                    <button id="surdo-w-mic-btn" class="surdo-w-mic-btn" title="Ovozli kiritish">🎤</button>
                    <button id="surdo-w-submit" class="surdo-w-submit-btn">O'girish</button>
                </div>
                <div class="surdo-w-chips">
                    <span class="surdo-w-chip" data-text="Assalomu alaykum">👋 Salom</span>
                    <span class="surdo-w-chip" data-text="Rahmat">🙏 Rahmat</span>
                    <span class="surdo-w-chip" data-text="O'zbekiston">🇺🇿 O'zbekiston</span>
                    <span class="surdo-w-chip" data-text="Ijtimoiy xizmat">🏛️ Xizmat</span>
                    <span class="surdo-w-chip" data-text="Zo'r">👍 Zo'r</span>
                </div>
            </div>
        </div>

        <!-- Matn belgilanganda ochiluvchi tezkor tooltip -->
        <div id="surdo-w-tooltip" class="surdo-w-selection-tooltip">
            <span>🤟</span> Surdo AI
        </div>
    `;
    document.body.appendChild(widgetContainer);

    // Elementlar
    const fab = document.getElementById('surdo-w-fab');
    const modal = document.getElementById('surdo-w-modal');
    const closeBtn = document.getElementById('surdo-w-close-btn');
    const expandBtn = document.getElementById('surdo-w-expand-btn');
    const video = document.getElementById('surdo-w-video');
    const caption = document.getElementById('surdo-w-caption');
    const statusBadge = document.getElementById('surdo-w-status');
    const input = document.getElementById('surdo-w-input');
    const submitBtn = document.getElementById('surdo-w-submit');
    const micBtn = document.getElementById('surdo-w-mic-btn');
    const speedBtn = document.getElementById('surdo-w-speed-btn');
    const tooltip = document.getElementById('surdo-w-tooltip');
    const langPills = document.querySelectorAll('.surdo-w-pill[data-lang]');

    let currentSpeed = 1.0;
    const speeds = [1.0, 1.25, 1.5];
    let activeQueue = [];
    let isPlaying = false;
    let fallbackTimer = null;

    // Vidjetni ochish / yopish
    function toggleModal(open) {
        if (open === undefined) open = !modal.classList.contains('open');
        if (open) {
            modal.classList.add('open');
            video.play().catch(() => {});
        } else {
            modal.classList.remove('open');
        }
    }

    fab.addEventListener('click', () => toggleModal());
    closeBtn.addEventListener('click', () => toggleModal(false));
    expandBtn.addEventListener('click', () => {
        modal.classList.toggle('expanded');
    });

    // Tezlikni o'zgartirish (1x -> 1.25x -> 1.5x)
    speedBtn.addEventListener('click', () => {
        const nextIdx = (speeds.indexOf(currentSpeed) + 1) % speeds.length;
        currentSpeed = speeds[nextIdx];
        speedBtn.textContent = `${currentSpeed}x`;
        if (video) video.playbackRate = currentSpeed;
    });

    // Til tugmalari
    langPills.forEach(pill => {
        pill.addEventListener('click', () => {
            langPills.forEach(p => p.classList.remove('active'));
            pill.classList.add('active');
        });
    });

    // Imo-ishora navbatini ijro etish tizimi
    function playQueue(items, fullLabel) {
        if (!items || items.length === 0) return;
        activeQueue = [...items];
        isPlaying = true;
        toggleModal(true);
        statusBadge.textContent = "Кўрсатилмоқда...";
        playNext(fullLabel);
    }

    function playNext(fullLabel) {
        clearTimeout(fallbackTimer);
        if (activeQueue.length === 0) {
            isPlaying = false;
            video.src = `${BASE_URL}/static/avatars/real_human_presenter.mp4`;
            video.loop = true;
            video.playbackRate = currentSpeed;
            video.play().catch(() => {});
            caption.textContent = fullLabel ? `Tugadi: "${fullLabel}"` : "Imo-ishora kutilmoqda...";
            statusBadge.textContent = "Tayyor...";
            return;
        }

        const item = activeQueue.shift();
        caption.textContent = item.label || fullLabel;
        video.src = item.video;
        video.loop = false;
        video.playbackRate = currentSpeed;
        video.currentTime = 0;
        video.play().catch(() => {});

        video.onended = () => {
            playNext(fullLabel);
        };

        // Zaxira vaqt tugmasi
        fallbackTimer = setTimeout(() => {
            if (isPlaying) playNext(fullLabel);
        }, 3500);
    }

    // Matnni imo-ishoraga o'girish (Lug'at + Daktil alifbosi)
    function translateTextToSigns(rawText) {
        if (!rawText || !rawText.trim()) return;
        const clean = rawText.trim();
        // Kirill bo'lsa avtomatik lotinlashtirish
        const latText = cyrillicToLatin(clean).toLowerCase();
        const words = latText.replace(/[.,\/#!$%\^&\*;:{}=\-_`~()?"'«»]/g, ' ').split(/\s+/).filter(w => w);

        const queue = [];
        words.forEach(word => {
            if (WIDGET_SIGN_DICT[word]) {
                queue.push(WIDGET_SIGN_DICT[word]);
            } else {
                // Agar butun so'z lug'atda bo'lmasa, uni daktil alifbosi (harfma-harf) ko'rsatish
                for (let i = 0; i < word.length; i++) {
                    const char = word[i].toUpperCase();
                    if (/^[A-Z]$/.test(char)) {
                        queue.push({
                            video: `${BASE_URL}/static/signs/letters/${char}.mp4`,
                            label: `${word} — ${char}`
                        });
                    }
                }
            }
        });

        if (queue.length > 0) {
            playQueue(queue, clean);
        } else {
            // Umumiy jonli imo-ishora ko'rsatish
            playQueue([{
                video: `${BASE_URL}/static/avatars/real_human_signing.mp4`,
                label: clean
            }], clean);
        }
    }

    // Submit tugmasi va Enter bosilganda
    submitBtn.addEventListener('click', () => {
        const val = input.value;
        if (val) translateTextToSigns(val);
    });
    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            const val = input.value;
            if (val) translateTextToSigns(val);
        }
    });

    // Tezkor so'z tugmalari
    document.querySelectorAll('.surdo-w-chip').forEach(chip => {
        chip.addEventListener('click', () => {
            const txt = chip.dataset.text;
            if (txt) {
                input.value = txt;
                translateTextToSigns(txt);
            }
        });
    });

    // Ovozli qidiruv (Web Speech Recognition)
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
        const recognizer = new SpeechRec();
        recognizer.continuous = false;
        recognizer.interimResults = false;
        recognizer.lang = 'uz-UZ';

        let isListening = false;
        micBtn.addEventListener('click', () => {
            if (isListening) {
                recognizer.stop();
            } else {
                try {
                    recognizer.start();
                    micBtn.classList.add('listening');
                    isListening = true;
                    statusBadge.textContent = "Tinglanmoqda...";
                } catch (e) {
                    console.warn(e);
                }
            }
        });

        recognizer.onresult = (evt) => {
            const transcript = evt.results[0][0].transcript;
            input.value = transcript;
            translateTextToSigns(transcript);
        };
        recognizer.onend = () => {
            micBtn.classList.remove('listening');
            isListening = false;
        };
        recognizer.onerror = () => {
            micBtn.classList.remove('listening');
            isListening = false;
        };
    } else {
        micBtn.style.display = 'none';
    }

    // Brauzerda matn tanlanganda (Selection Tooltip)
    let selectedTextToSign = '';
    document.addEventListener('mouseup', (e) => {
        if (e.target.closest('#surdo-ai-widget-root')) return;

        const sel = window.getSelection();
        const text = sel ? sel.toString().trim() : '';

        if (text && text.length > 1) {
            selectedTextToSign = text;
            const range = sel.getRangeAt(0);
            const rect = range.getBoundingClientRect();

            tooltip.style.left = `${window.scrollX + rect.left + (rect.width / 2) - 40}px`;
            tooltip.style.top = `${window.scrollY + rect.top - 36}px`;
            tooltip.style.display = 'flex';
        } else {
            setTimeout(() => {
                tooltip.style.display = 'none';
            }, 150);
        }
    });

    tooltip.addEventListener('click', (e) => {
        e.stopPropagation();
        tooltip.style.display = 'none';
        if (selectedTextToSign) {
            input.value = selectedTextToSign;
            translateTextToSigns(selectedTextToSign);
        }
    });

    console.log("Surdo AI Vidjeti muvaffaqiyatli ishga tushdi!");
})();
