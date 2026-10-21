# claude-motion-film · 12 秒宣传片 v2

主题：讲这个 skill 是怎么来的，并让人看完想装。
母题：**一个点**——句号 → 实心圆 → 窗口 → 塌成一条线 → 收成点 → 炸成 900 颗粒子 → 引力流 → 聚合成字形。

## 规格（ffprobe 实测于交付文件）
```
h264 High · 1920x1080 · 30/1 fps · yuv420p · 360 帧 · 12.000000 s · 26.0 MB
aac 48000 Hz · 2 ch
I = -15.1 LUFS · True peak = -1.3 dBFS
```

## 时间表（120 BPM · 6 小节 × 2s）
| 时间 | 画面 | 文案 |
|---|---|---|
| 0.00–2.00 | 一颗点淡入、呼吸四拍 | 一句话。 |
| 2.00–4.00 | 点砸成实心圆 → 变成 16:9 窗口；八分音符上翻倍 | 一支片。 |
| 4.00–6.00 | 窗口里 900 根柱读成音频波形，计数器 0→900 | 900 帧。 |
| 6.00–8.00 | **最大冲击**：光爆 + 900 根塌成一条发丝线 | 一条线。 |
| 8.00–10.00 | 线收成点 → **炸成 900 颗粒子** → 沿带状脊线做引力流 | 任何主题。 |
| 10.00–12.00 | 粒子**聚合成 "claude"** → 真字落在同坐标 → 下划线 + CTA | 装上它。 |

## v2 针对反馈改了什么
| 反馈 | 处理 |
|---|---|
| 音乐中间/结尾突然没声 | **删掉 `build_gate` 的 ×0**。三段改为"悬停"：床下潜 −18dB + 低通 8k→400Hz 关闭 + 12s 不断的 sub drone + 反向混响吸进下一击；结尾 300ms 余弦释放。实测交付文件 **0 个 100ms 窗口低于 −45dB**（最小 −32.64dB） |
| 音效能力 | 每记 impact 固定五层（sub/body/crack/slap/tail）；新增 9 种音色（glass_crack / gran_cluster / shimmer / flow_air / tape_stop / rev_swell / air_bed / air_puff / blip_down / drone） |
| 色散能增加质感 | 改为**常驻基底 2.4px + 冲击尖峰 8–11px**，落版段回落到 1.2px 保字清晰。之前"关闭色散"是判断错误 |
| 素材单调 | 新增 900 粒子系统：爆裂 → 带状引力流 → 最小位移回流成字形 → 墨水覆盖。母题从"一条竖线"升级为"一个点"的六级变形 |
| 冲击画面沉浸感 | 保留 3 处光爆（2.00 / 6.00 / 10.00），并让 6.00 仍是全集最大一击 |

## 验收（全部对交付文件实测）
| 门 | 结果 |
|---|---|
| 帧数 / 时长 | 360 / 12.000000 s ✓ |
| 硬切 | 0 次。scene 分 >0.90 的**只有 3 帧**（f60/180/300），经查证是光爆，非切点 |
| 音乐连续 | 120 个 100ms 窗口，最小 −32.64 dBFS，**低于 −45dB 的 0 个** ✓ |
| 响度 | I = −15.1 LUFS，TP = −1.3 dBTP ✓ |
| 音画对位 | 8 个事件起音偏差 ≤5 ms |
| 留白 | 稳定帧墨迹 ≤11.2%；3 帧光爆例外（已单独测量记录） |
| 解码 | 全片 0 错误 0 警告 |
| 文案 | 全分辨率裁切逐句看过，无重叠压字 |

## 文件
`out/claude-motion-film.mp4` 成片 · `timeline.py` 唯一真相源 · `particles.py` 粒子系统（流场+字形回流） · `gfx.py` `common.py` `scenes.py` `render.py` 画面 · `audio.py` 配乐与母带 · `out/audio-report.md` 音频证据 · `out/agg_01.png` 粒子聚合审片表

## 重建
```
python particles.py      # 预计算流场与字形靶点（0.2s）
python render.py all     # 360 帧，12 进程，约 47s
ffmpeg -i out/video_silent.mp4 -i out/soundtrack.wav -c:v copy -c:a aac -b:a 320k \
       -ar 48000 -ac 2 -shortest -movflags +faststart out/claude-motion-film.mp4
python audio.py          # 重新合成音轨
```

## 我没做到的
1. **没有人耳听过音轨**，全部为数值自检。
2. 60Hz 以下仍占约 28% 能量，手机外放偏薄，靠 mid slap 撑。
3. 悬停是 −18dB 下潜，床确实会退；要绝对平可把 `DODGE_DB` 设 0，但"屏住呼吸"就没了。
4. 混响是合成卷积，无真实空间；无侧链、无总线压缩；24bit 无抖动。
5. 字号跨度 27.8×，未达自定的 30×。
## v3 - particles rebuilt against the Canvas reference
Reference: https://flipped.yourturns.cc/text/ - four principles adopted:
1. **Pixel-grid sampling** (one particle per 4 px cell) - density 900 -> **9000**. Density is
   the only reason a glyph reads at all.
2. **True round dots**: sigma 0.90 gaussian, diameter about equal to the sampling step, so dots
   tile the lattice.
3. **Phosphor trail**: the reference never clears its canvas (`rgba(bg,0.18)` fill); a pure
   function of time reconstructs it from **4 time taps** (0 / 22 / 44 / 70 ms).
4. **Tone-mapped accumulation** `a/(1+0.85a)`: without it the dense interior flattens to a
   white slab and only the edges keep any grain.

Real bug fixed along the way: the frame buffer is 0..1 but the particle layer multiplied by
the 0..255 `TL.CREAM` tuple, clipping every particle to white - which looked exactly like
'too high a density'.
## v4 - brightness-mask handoff
- 聚合压缩到 0.62s（DELAY 0–0.14），粒子**先稳定**，墨水 gated 在 11.02 之后才出现。
- 三拍交接：**assemblage（点阵成形）→ bloom+hold（增益 ×1.6，累积削平，点盖住字）→ dim（增益归零，真字显形）**。
  粒子是加性叠在文字之上的，所以**亮度本身就是遮罩**，全程无交叉溶解、无双影。
- 亮度按实测反推：p90 = 0.141 → 增益 4.6 让典型点是 0.65 满量程（原来是 2.7，偏暗）。
- 记录一个坑：`blur()` 的半径是量化的，σ1.15 与 σ1.30 输出**完全相同**——"点太小"其实是"点太暗"。
- CTA 提前到 11.08，让橙色句号在最后一击前落定。
## v5 - flash-cut swap（按指定流程）
流程：粒子完全合并 → 提亮到峰值（增益 ×2.2）→ **全屏闪白**（攻击 60ms，峰值落在第 331 帧，衰减 τ=75ms）
→ **在闪白最亮的那一帧**立刻关掉粒子、立刻满亮度贴上真文字 → 白色褪去，真字已经在那儿。

- 真文字**零入场动效**：去掉了原来的 0.30s 垂直模糊揭示与 16px 上移，改为硬切满不透明度。
- 峰值对齐全帧：`P_FLASH = 331/30`，闪白帧 = 换字帧，子帧错位就会露缝。
- 之前的"亮度当遮罩 + 调暗显形"被否了——它留下可辨的衔接痕迹，改用闪白切。
- CTA 移到 11.24，让「装上它。」在片尾前完整落定。
## v6 - 16 秒版
- 时长 12s → **16.000s / 480 帧 / 8 小节**。多出的 4 秒全部给粒子漫游（8.00–12.00），聚合点从 10.00 推到 **12.00**。
- 闪白改为**带平台**：攻击 60ms → **纯白保持 3 帧（f386–f388）** → 衰减；真字在平台第一帧（f386）写入。
- 粒子汇聚曲线换成 `cubic-bezier(0.71,0,0.99,0.52)`（强 ease-in，被吸引的加速感）。
- 转场全部由场景内现存元素承担：点→圆→窗口（同一半径变量）、窗口→发丝线（竖向塌缩）、线→点→粒子（同一位置爆裂）、粒子→字形（最小位移+垂直弧）。没有引入任何新素材。
- 音频重做为 16s：8 小节 Am|F|C|G|Am|F|F9|G7，6 个冲击对位偏差 0.0ms，12.8667 闪白帧单独给了 flash_hit。
- 编码头修正：wav −1.40 dBTP，AAC 后顶到 −0.7 超限；加 `-af volume=-0.45dB` 后落在 −1.3 dBTP / −15.4 LUFS。

### 终检（对交付文件实测）
```
480 帧 · 16.000000s · 1920x1080 30fps · yuv420p · AAC 48k 立体声 · 34.1 MB
I = -15.4 LUFS · True peak = -1.3 dBFS
100ms 窗口 160 个，最小 -33.58 dBFS，低于 -45dB 的 0 个
解码 0 错误
```
## v7 - 闪白改为瞬间到峰值
- 去掉攻击斜坡：f386 第一帧就是纯白（0→1 在一帧内），保持 3 帧，之后才是衰减。
- 粒子延迟收到 DELAY_MAX=0.06 → f384/f385 实测残余距离 1.3/1.2px、**0 颗粒子在动**，
  即 f385 已完全合并，f386 闪白与换字同帧发生。
- 用数值验证而不是肉眼：`max(||positions(t)-targets||) < 2px` 才算合并完成。
## v8 - 闪白峰值锁定 12s25f
- 峰值帧 f385 = **12s25f** = 12.8333s。实测 f384 残余 1.3px 且 0 颗粒子在动，即合并完成。
- 逐帧平均亮度实测：f384 = 24.7 → **f385 = 227.1（一帧跳 +202）** → f386/f387 = 227.1 → f388 = 166.0 起渐暗。
- 无攻击段；平台 3 帧；只有衰减有过渡。音频 flash_hit 在 12.8667，与画面峰值差 1 帧（33ms，在 ±60ms 预算内）。
- 定位方法已固化：① 粒子残余距离判「合并完成帧」；② 160x90 灰度逐帧均值判「闪白峰值帧」。