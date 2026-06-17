# Nike Adapt — CoreRF / Bigfoot BLE protocol

Reverse-engineered from the official **`com.nike.adapt`** Android APK
(`com.nike.adapt_1.24.0`, decompiled with **jadx**). The Android build is far
easier to read than the iOS `Bigfoot.framework` ARM binary, and it gives the
*exact* framing, opcodes, and authentication flow — this is the ground truth
that the earlier 98 brute-force probes never reached.

Target hardware: **Nike Adapt Auto Max (CZ6799-001)**, firmware `2.4.3M`.

---

## 1. BLE GATT (class `xa.a0` — CoreRFConstants)

| Role | UUID |
|------|------|
| Service ("Ripley") | `1A2328AF-3D0B-4B04-A2AA-973C239D3904` |
| Write characteristic | `226BAEA6-1543-40C2-8EAE-A69B02171B08` (`writeWithoutResponse`, `write`) |
| Notify characteristic | `30C4142F-B083-42CF-865A-D5B91801BCD7` (`notify`, `read`) |
| CCCD descriptor | `00002902-…` |
| Battery service / level | `0000180F-…` / `00002A19-…` (standard, no auth needed) |

The shoe advertises its BLE name as `EARL LEFT` / `EARL RIGHT`.

---

## 2. Three protocol layers

```
┌──────────────────────────────────────────────┐
│ Application : protobuf payloads (Bigfoot.proto)│
├──────────────────────────────────────────────┤
│ CoreRF frame: [opcode][len][type]  (Message.java)
├──────────────────────────────────────────────┤
│ Ripley transport: 19-byte segments  (TransportScatter)
└──────────────────────────────────────────────┘
        BLE writeWithoutResponse, ≤ 20 bytes / packet
```

### 2a. CoreRF message frame — `com.nike.corerf.bigfoot.f`

```
byte 0      opcode
byte 1      length & 0xFF              (length of the protobuf payload)
byte 2      (length >> 8) | (type << 6)   bits 6-7 = message type, bits 0-5 = length high
byte 3..    protobuf payload
```

`type`: `REQUEST=0`, `ACK=1`, `NAK=2`, `EVENT=3`.

> The Java writes `Short.reverseBytes((length & 0x3FFF) | (type << 14))` with a
> big-endian `putShort`, which is just the little-endian encoding above.

### 2b. Ripley segmentation — `xa.h0.b` + `com.nike.corerf.bigfoot.c`

The framed message is cut into **≤ 19-byte** chunks. Each BLE packet is:

```
byte 0      header = sequence (mod 64) in bits 0-5
            · bit 0x80  → LAST segment of the message
            · bit 0x40  → flow-control packet (not application data)
byte 1..    up to 19 bytes of framed data
```

* The **sequence counter is a rolling `mod 64` value that continues across
  messages** (reset to 0 on each new connection). It is **not** `segIndex<<1|last`.
* Receiving is the mirror image: strip the 1-byte header from each packet,
  concatenate the data, and when a packet has `0x80` set the message is complete
  → run the CoreRF de-frame.
* **Flow control**: a packet whose header has `0x40` set (e.g. the shoe's
  periodic `C0 xx`) is a transport keepalive / window update, **not** an
  application message. Earlier work mistook `C0 01` for `StartAuthKeyGen`; it is
  actually just a Ripley keepalive. The phone does not need to send flow-control
  acks for short messages (the shoe only stalls once ≥ 4 segments are
  outstanding, far more than auth/lacing/LED ever use).

### 2c. Opcodes — `com.nike.corerf.bigfoot.b` (BigfootOperationCode)

| Opcode | Dec | Hex | Payload (Bigfoot.proto) |
|--------|-----|-----|--------------------------|
| `SERVO_MOVE` | 0 | 0x00 | `ServoMove{ command }` |
| `SERVO_POSITION_SET` | 3 | 0x03 | `ServoPosition{ positionPercentage }` |
| `SERVO_POSITION_GET` | 4 | 0x04 | → `ServoPosition` |
| `SERVO_MOVE_COMPLETE_EVENT` | 5 | 0x05 | `ServoStatusEvent{ status, positionPercentage }` |
| `IDENTIFY` | 20 | 0x14 | — |
| `SERIAL_NUMBER_GET` | 50 | 0x32 | `GetSerialNumber` |
| `BATTERY_CHARGER_STATE_GET` | 81 | 0x51 | → `BatteryChargerState` |
| `TOGGLE_FPS` | 82 | 0x52 | `ToggleFPS{ turnFpsOn }` |
| `START_AUTHENTICATION` | 112 | 0x70 | `StartAuthenticationRequest{ phoneNonce }` |
| `AUTHENTICATION_CHALLENGE` | 113 | 0x71 | `AuthenicationChallenge{ encryptedDeviceNonce }` |
| `SET_LED_BASE` | 130 | 0x82 | `SetLEDBase{ r,g,b,brightness }` (fw < 2.1.7) |
| `ANIMATION_SET_COLOR` | 222 | 0xDE | `AnimationColor{ color_id, r,g,b }` (fw ≥ 2.1.7) |

`ServoMove.ServoCommand`: `HOME=0, SHORT_TIGHTEN=1, LONG_TIGHTEN=2,
SHORT_LOOSEN=3, LONG_LOOSEN=4, MAX_TIGHTEN=5, MAX_LOOSEN=6, AUTOLACE=7, STOP=8,
HUG=9`.

---

## 3. Authentication — challenge/response, **not** Diffie-Hellman

Source: `xa.g.r()` (orchestration), `r0.v` (start), `i4.u` (challenge).

There are **two distinct auth flows** (per the `Bigfoot.proto` comments):

* **Imprinting** (`START_AUTH_KEY_GENERATION` + `EXCHANGE_PUBLIC_KEY`) — DH
  Group 2, run **once** when first pairing, to *generate* the shared key.
  `authKey = MD5(DH_shared_secret)` (`xa.l`).
* **Authentication** (`START_AUTHENTICATION` + `AUTHENTICATION_CHALLENGE`) — run
  **on every connection**, using the already-imprinted key.

Since we already hold the imprinted per-shoe `authKey` (extracted from the iOS
app), we **skip DH entirely** and do only the per-connection challenge:

```
1. phoneNonce  = 16 random bytes
2. →  START_AUTHENTICATION  REQUEST   StartAuthenticationRequest{ phoneNonce = field 1 }
3. ←  START_AUTHENTICATION  ACK       StartAuthenticationACK{ encryptedPhoneNonce = 1,
                                                              deviceNonce         = 2 }
      (we ignore field 1, take deviceNonce = field 2; both 16 bytes)
4.    encryptedDeviceNonce = AES-128-ECB-NoPadding( key = authKey, data = deviceNonce )
5. →  AUTHENTICATION_CHALLENGE REQUEST AuthenicationChallenge{ encryptedDeviceNonce = field 1 }
6. ←  AUTHENTICATION_CHALLENGE ACK  ⇒ authenticated
```

The AES is plain **AES-128-ECB / NoPadding** on the single 16-byte nonce block
(`i4.u`: `Cipher.getInstance("AES/ECB/NoPadding")`, key = `authKey`). In
WebCrypto this is reproduced as AES-CBC with a zero IV, taking the first 16-byte
block of the output.

If `authKey == {0x01}×16` (the firmware `DEFAULT_KEY`), the app falls back to the
DH imprinting flow first — not needed here.

### Per-shoe data (extracted from the iOS app)

| | Left (`EARL LEFT`) | Right (`EARL RIGHT`) |
|---|---|---|
| authKey | `9052f05b19c5720cd8870c0935301f38` | `fe52d2d20e321e3bc327792987ea9958` |
| max tightness | 58 | 54 |

---

## 4. Worked example — START_AUTHENTICATION on the wire

```
protobuf  : 0A 10 <16-byte phoneNonce>                     (18 bytes)
CoreRF    : 70 12 00  0A 10 <…phoneNonce…>                 (21 bytes; type REQUEST, len 18)
Ripley    : seg0  [00]  70 12 00 0A 10 <first 14 nonce B>  (20 bytes, seq 0)
            seg1  [81]  <last 2 nonce bytes>               (3 bytes, seq 1 | LAST)
```

The 39-byte `StartAuthenticationACK` comes back as **3** Ripley segments to
reassemble before de-framing.

---

## 5. Implementation

`docs/index.html` (the PWA) implements all of the above in
`corerfFrame` / `corerfParse`, `pbVarint`/`pbBytes`/`pbDecode`, and the
`NikeShoe` methods `_sendMessage` / `_writeFramed` / `_notify` / `_auth`.

Decompiled reference sources live under `../decompiled/sources/` (not committed):
`com/nike/corerf/bigfoot/{b,c,f}.java`, `xa/{g,h0,a0,l,q}.java`, `i4/u.java`,
`r0/v.java`.
