#include <Arduino.h>
// Teensy SPI (hardware SPI0)
#include <SPI.h>

#define TOGGLE_TEST 0

// Teensy 4.1 SPI0: MOSI=11, MISO=12, SCK=13. CS=10 per mapping
#define TEENSY_SPI_CS 10
// ISOMD mode select pin routed to Teensy GPIO per usage.ato: Teensy gpio[41]
#define PIN_ISOMD 41

SPISettings settings(400000, MSBFIRST, SPI_MODE3);

static void wakeup()
{
    // Common wake-up: CS toggle and preamble bytes
    digitalWrite(TEENSY_SPI_CS, HIGH);
    delayMicroseconds(10);
    digitalWrite(TEENSY_SPI_CS, LOW);
    delayMicroseconds(10);
    digitalWrite(TEENSY_SPI_CS, HIGH);
    delay(2);
    SPI.beginTransaction(settings);
    digitalWrite(TEENSY_SPI_CS, LOW);
    uint8_t pre[4] = {0xFF, 0xFF, 0xFF, 0xFF};
    SPI.transfer(pre, sizeof(pre));
    digitalWrite(TEENSY_SPI_CS, HIGH);
    SPI.endTransaction();
}

// Commands and constants
#define ADBMS6948_SHIFT_BY_8 ((uint8_t)8u)
#define ADBMS6948_RDALL_CELLVOLTAGES_BYTES ((uint8_t)34u)
#define DATA_LEN ((uint8_t)0x04u)
#define ADBMS6948_REG_DATA_LEN_WITH_PEC ((uint8_t)0x08u)
#define ADBMS6948_MAX_NO_OF_DEVICES_IN_DAISY_CHAIN (1U)
#define ADBMS6948_REG_GRP_LEN ((uint8_t)0x06u)

// Register map
#define ADCV ((uint16_t)0x0260u)
#define ADSV ((uint16_t)0x0168u)
#define ADI1 ((uint16_t)0x0200u)
#define ADI2 ((uint16_t)0x0108u)
#define ADCIV ((uint16_t)0x240u)
#define ADAX ((uint16_t)0x0410u)
#define ADAX2 ((uint16_t)0x0400u)
#define MUTE ((uint16_t)0x0028u)
#define UNMUTE ((uint16_t)0x0029u)
#define RDACALL ((uint16_t)0x004Cu)
#define WRCFGA ((uint16_t)0x0001u)
#define WRCFGB ((uint16_t)0x0024u)
#define WRCFGC ((uint16_t)0x0081u)
#define WRCFGD ((uint16_t)0x00A4u)
#define WRCFGE ((uint16_t)0x0073u)
#define WRCFGF ((uint16_t)0x0075u)
#define WRCFGG ((uint16_t)0x0077u)
#define WRCFGH ((uint16_t)0x0079u)
#define WRCFGI ((uint16_t)0x007Bu)
#define RDCFGA ((uint16_t)0x0002u)
#define RDCFGB ((uint16_t)0x0026u)
#define RDCFGC ((uint16_t)0x0082u)
#define RDCFGD ((uint16_t)0x00A6u)
#define RDCFGE ((uint16_t)0x0074u)
#define RDCFGF ((uint16_t)0x0076u)
#define RDCFGG ((uint16_t)0x0078u)
#define RDCFGH ((uint16_t)0x007Au)
#define RDCFGI ((uint16_t)0x007Cu)

// CADC Registers
#define RDCVA ((uint16_t)0x0004u)
#define RDCVB ((uint16_t)0x0006u)
#define RDCVC ((uint16_t)0x0008u)
#define RDCVD ((uint16_t)0x000Au)
#define RDCVE ((uint16_t)0x0009u)
#define RDCVF ((uint16_t)0x000Bu)
#define RDCVALL ((uint16_t)0x000Cu)

// SADC Registers
#define RDSVA ((uint16_t)0x0003u)
#define RDSVB ((uint16_t)0x0005u)
#define RDSVC ((uint16_t)0x0007u)
#define RDSVD ((uint16_t)0x000Du)
#define RDSVE ((uint16_t)0x000Eu)
#define RDSVF ((uint16_t)0x000Fu)
#define RDSVALL ((uint16_t)0x0010u)

// CADC Filtered Registers
#define RDFCA ((uint16_t)0x0012u)
#define RDFCB ((uint16_t)0x00013u)
#define RDFCC ((uint16_t)0x0014u)
#define RDFCD ((uint16_t)0x0015u)
#define RDFCE ((uint16_t)0x0016u)
#define RDFCF ((uint16_t)0x0017u)
#define RDFCALL ((uint16_t)0x0018u)

// AUX Registers
#define RDAUXA ((uint16_t)0x0019u)
#define RDAUXB ((uint16_t)0x001Au)
#define RDAUXC ((uint16_t)0x001Bu)
#define RDAUXD ((uint16_t)0x001Fu)

// ID Register
#define RDSID ((uint16_t)0x002C)

// Balance PWM Registers
#define WRPWMA ((uint16_t)0x0020u)
#define RDPWMA ((uint16_t)0x0022u)
#define WRPWMB ((uint16_t)0x0021u)
#define RDPWMB ((uint16_t)0x0023u)

/* Pre-computed CRC15 Table */
static const uint16_t Adbms6948_Crc15Table[256] =
    {
        0x0u, 0xc599u, 0xceabu, 0xb32u, 0xd8cfu, 0x1d56u, 0x1664u, 0xd3fdu, 0xf407u, 0x319eu, 0x3aacu,
        0xff35u, 0x2cc8u, 0xe951u, 0xe263u, 0x27fau, 0xad97u, 0x680eu, 0x633cu, 0xa6a5u, 0x7558u, 0xb0c1u,
        0xbbf3u, 0x7e6au, 0x5990u, 0x9c09u, 0x973bu, 0x52a2u, 0x815fu, 0x44c6u, 0x4ff4u, 0x8a6du, 0x5b2eu,
        0x9eb7u, 0x9585u, 0x501cu, 0x83e1u, 0x4678u, 0x4d4au, 0x88d3u, 0xaf29u, 0x6ab0u, 0x6182u, 0xa41bu,
        0x77e6u, 0xb27fu, 0xb94du, 0x7cd4u, 0xf6b9u, 0x3320u, 0x3812u, 0xfd8bu, 0x2e76u, 0xebefu, 0xe0ddu,
        0x2544u, 0x02beu, 0xc727u, 0xcc15u, 0x098cu, 0xda71u, 0x1fe8u, 0x14dau, 0xd143u, 0xf3c5u, 0x365cu,
        0x3d6eu, 0xf8f7u, 0x2b0au, 0xee93u, 0xe5a1u, 0x2038u, 0x07c2u, 0xc25bu, 0xc969u, 0x0cf0u, 0xdf0du,
        0x1a94u, 0x11a6u, 0xd43fu, 0x5e52u, 0x9bcbu, 0x90f9u, 0x5560u, 0x869du, 0x4304u, 0x4836u, 0x8dafu,
        0xaa55u, 0x6fccu, 0x64feu, 0xa167u, 0x729au, 0xb703u, 0xbc31u, 0x79a8u, 0xa8ebu, 0x6d72u, 0x6640u,
        0xa3d9u, 0x7024u, 0xb5bdu, 0xbe8fu, 0x7b16u, 0x5cecu, 0x9975u, 0x9247u, 0x57deu, 0x8423u, 0x41bau,
        0x4a88u, 0x8f11u, 0x057cu, 0xc0e5u, 0xcbd7u, 0x0e4eu, 0xddb3u, 0x182au, 0x1318u, 0xd681u, 0xf17bu,
        0x34e2u, 0x3fd0u, 0xfa49u, 0x29b4u, 0xec2du, 0xe71fu, 0x2286u, 0xa213u, 0x678au, 0x6cb8u, 0xa921u,
        0x7adcu, 0xbf45u, 0xb477u, 0x71eeu, 0x5614u, 0x938du, 0x98bfu, 0x5d26u, 0x8edbu, 0x4b42u, 0x4070u,
        0x85e9u, 0x0f84u, 0xca1du, 0xc12fu, 0x04b6u, 0xd74bu, 0x12d2u, 0x19e0u, 0xdc79u, 0xfb83u, 0x3e1au, 0x3528u,
        0xf0b1u, 0x234cu, 0xe6d5u, 0xede7u, 0x287eu, 0xf93du, 0x3ca4u, 0x3796u, 0xf20fu, 0x21f2u, 0xe46bu, 0xef59u,
        0x2ac0u, 0x0d3au, 0xc8a3u, 0xc391u, 0x0608u, 0xd5f5u, 0x106cu, 0x1b5eu, 0xdec7u, 0x54aau, 0x9133u, 0x9a01u,
        0x5f98u, 0x8c65u, 0x49fcu, 0x42ceu, 0x8757u, 0xa0adu, 0x6534u, 0x6e06u, 0xab9fu, 0x7862u, 0xbdfbu, 0xb6c9u,
        0x7350u, 0x51d6u, 0x944fu, 0x9f7du, 0x5ae4u, 0x8919u, 0x4c80u, 0x47b2u, 0x822bu, 0xa5d1u, 0x6048u, 0x6b7au,
        0xaee3u, 0x7d1eu, 0xb887u, 0xb3b5u, 0x762cu, 0xfc41u, 0x39d8u, 0x32eau, 0xf773u, 0x248eu, 0xe117u, 0xea25u,
        0x2fbcu, 0x0846u, 0xcddfu, 0xc6edu, 0x0374u, 0xd089u, 0x1510u, 0x1e22u, 0xdbbbu, 0x0af8u, 0xcf61u, 0xc453u,
        0x01cau, 0xd237u, 0x17aeu, 0x1c9cu, 0xd905u, 0xfeffu, 0x3b66u, 0x3054u, 0xf5cdu, 0x2630u, 0xe3a9u, 0xe89bu,
        0x2d02u, 0xa76fu, 0x62f6u, 0x69c4u, 0xac5du, 0x7fa0u, 0xba39u, 0xb10bu, 0x7492u, 0x5368u, 0x96f1u, 0x9dc3u,
        0x585au, 0x8ba7u, 0x4e3eu, 0x450cu, 0x8095u};

/* Pre-computed CRC10 Table */
static const uint16_t Adbms6948_Crc10Table[256] =
    {
        0x000, 0x08f, 0x11e, 0x191, 0x23c, 0x2b3, 0x322, 0x3ad, 0x0f7, 0x078, 0x1e9, 0x166, 0x2cb, 0x244, 0x3d5, 0x35a,
        0x1ee, 0x161, 0x0f0, 0x07f, 0x3d2, 0x35d, 0x2cc, 0x243, 0x119, 0x196, 0x007, 0x088, 0x325, 0x3aa, 0x23b, 0x2b4,
        0x3dc, 0x353, 0x2c2, 0x24d, 0x1e0, 0x16f, 0x0fe, 0x071, 0x32b, 0x3a4, 0x235, 0x2ba, 0x117, 0x198, 0x009, 0x086,
        0x232, 0x2bd, 0x32c, 0x3a3, 0x00e, 0x081, 0x110, 0x19f, 0x2c5, 0x24a, 0x3db, 0x354, 0x0f9, 0x076, 0x1e7, 0x168,
        0x337, 0x3b8, 0x229, 0x2a6, 0x10b, 0x184, 0x015, 0x09a, 0x3c0, 0x34f, 0x2de, 0x251, 0x1fc, 0x173, 0x0e2, 0x06d,
        0x2d9, 0x256, 0x3c7, 0x348, 0x0e5, 0x06a, 0x1fb, 0x174, 0x22e, 0x2a1, 0x330, 0x3bf, 0x012, 0x09d, 0x10c, 0x183,
        0x0eb, 0x064, 0x1f5, 0x17a, 0x2d7, 0x258, 0x3c9, 0x346, 0x01c, 0x093, 0x102, 0x18d, 0x220, 0x2af, 0x33e, 0x3b1,
        0x105, 0x18a, 0x01b, 0x094, 0x339, 0x3b6, 0x227, 0x2a8, 0x1f2, 0x17d, 0x0ec, 0x063, 0x3ce, 0x341, 0x2d0, 0x25f,
        0x2e1, 0x26e, 0x3ff, 0x370, 0x0dd, 0x052, 0x1c3, 0x14c, 0x216, 0x299, 0x308, 0x387, 0x02a, 0x0a5, 0x134, 0x1bb,
        0x30f, 0x380, 0x211, 0x29e, 0x133, 0x1bc, 0x02d, 0x0a2, 0x3f8, 0x377, 0x2e6, 0x269, 0x1c4, 0x14b, 0x0da, 0x055,
        0x13d, 0x1b2, 0x023, 0x0ac, 0x301, 0x38e, 0x21f, 0x290, 0x1ca, 0x145, 0x0d4, 0x05b, 0x3f6, 0x379, 0x2e8, 0x267,
        0x0d3, 0x05c, 0x1cd, 0x142, 0x2ef, 0x260, 0x3f1, 0x37e, 0x024, 0x0ab, 0x13a, 0x1b5, 0x218, 0x297, 0x306, 0x389,
        0x1d6, 0x159, 0x0c8, 0x047, 0x3ea, 0x365, 0x2f4, 0x27b, 0x121, 0x1ae, 0x03f, 0x0b0, 0x31d, 0x392, 0x203, 0x28c,
        0x038, 0x0b7, 0x126, 0x1a9, 0x204, 0x28b, 0x31a, 0x395, 0x0cf, 0x040, 0x1d1, 0x15e, 0x2f3, 0x27c, 0x3ed, 0x362,
        0x20a, 0x285, 0x314, 0x39b, 0x036, 0x0b9, 0x128, 0x1a7, 0x2fd, 0x272, 0x3e3, 0x36c, 0x0c1, 0x04e, 0x1df, 0x150,
        0x3e4, 0x36b, 0x2fa, 0x275, 0x1d8, 0x157, 0x0c6, 0x049, 0x313, 0x39c, 0x20d, 0x282, 0x12f, 0x1a0, 0x031, 0x0be};

uint16_t calculatePEC15(uint8_t *pDataBuf, uint8_t nLength)
{
    uint16_t nRemainder, nTableAddr;
    uint8_t nByteIndex;

    nRemainder = 16u; /* initialize the PEC */

    /* loops for each byte in data array */
    for (nByteIndex = 0u; nByteIndex < nLength; nByteIndex++)
    {
        /* calculate PEC table address */
        nTableAddr = (uint16_t)(((uint16_t)(nRemainder >> 7) ^ (uint8_t)pDataBuf[nByteIndex]) &
                                (uint8_t)0xff);
        nRemainder = (uint16_t)((nRemainder << 8) ^ Adbms6948_Crc15Table[nTableAddr]);
    }
    /* The CRC15 has a 0 in the LSB so the remainder must be multiplied by 2 */
    return (nRemainder * 2u);
}

uint16_t calculatePEC10(uint8_t *pDataBuf, uint8_t nLength, boolean bIsRxCmd)
{
    uint16_t nRemainder = 16u; /* PEC_SEED */
    /* x10 + x7 + x3 + x2 + x + 1 <- the CRC10 polynomial 100 1000 1111 */
    uint16_t nPolynomial = 0x8Fu;
    uint8_t nByteIndex, nBitIndex;
    uint16_t nTableAddr;

    for (nByteIndex = 0u; nByteIndex < nLength; ++nByteIndex)
    {
        /* calculate PEC table address */
        nTableAddr = (uint16_t)(((uint16_t)(nRemainder >> 2) ^ (uint8_t)pDataBuf[nByteIndex]) &
                                (uint8_t)0xff);
        nRemainder = (uint16_t)(((uint16_t)(nRemainder << 8)) ^ Adbms6948_Crc10Table[nTableAddr]);
    }
    /* If array is from received buffer add command counter to crc calculation */
    if (bIsRxCmd == true)
    {
        nRemainder ^= (uint16_t)(((uint16_t)pDataBuf[nLength] & (uint8_t)0xFC) << 2u);
    }
    /* Perform modulo-2 division, a bit at a time */
    for (nBitIndex = 6u; nBitIndex > 0u; --nBitIndex)
    {
        /* Try to divide the current data bit */
        if ((nRemainder & 0x200u) > 0u)
        {
            nRemainder = (uint16_t)((nRemainder << 1u));
            nRemainder = (uint16_t)(nRemainder ^ nPolynomial);
        }
        else
        {
            nRemainder = (uint16_t)((nRemainder << 1u));
        }
    }
    return ((uint16_t)(nRemainder & 0x3FFu));
}

void sendCommand(uint16_t nCommand)
{
    uint16_t nCmdPec;
    uint8_t aCmd[0x04u];

    aCmd[0] = (uint8_t)((nCommand & 0xFF00u) >> ADBMS6948_SHIFT_BY_8);
    aCmd[1] = (uint8_t)((nCommand & 0x00FFu));
    /* Calculate the 15-bit PEC for the command bytes */
    nCmdPec = (uint16_t)calculatePEC15(&aCmd[0], 2u);
    /* Append the PEC to the command buffer */
    aCmd[2] = (uint8_t)(nCmdPec >> ADBMS6948_SHIFT_BY_8);
    aCmd[3] = (uint8_t)(nCmdPec);

    // Start SPI transaction
    SPI.beginTransaction(settings);
    digitalWrite(TEENSY_SPI_CS, LOW);
    SPI.transfer(aCmd, sizeof(aCmd));
    // End SPI transaction
    digitalWrite(TEENSY_SPI_CS, HIGH);
    SPI.endTransaction();
}

void writeData(uint16_t nCommand, uint8_t *pTxBuf, uint8_t len)
{
    uint16_t nCmdPec;
    uint8_t bufferSize = 4 + len + 2;
    uint8_t aCmd[bufferSize];

    // Populate the command part of the buffer
    aCmd[0] = (uint8_t)((nCommand & 0xFF00u) >> ADBMS6948_SHIFT_BY_8);
    aCmd[1] = (uint8_t)((nCommand & 0x00FFu));

    // Calculate the 15-bit PEC for the command bytes
    nCmdPec = (uint16_t)calculatePEC15(&aCmd[0], 2u);

    // Append the PEC to the command buffer
    aCmd[2] = (uint8_t)(nCmdPec >> ADBMS6948_SHIFT_BY_8);
    aCmd[3] = (uint8_t)(nCmdPec);

    // Append the data to the command buffer
    for (int i = 0; i < len; i++)
    {
        aCmd[4 + i] = pTxBuf[i];
    }

    // Calculate the PEC for the data
    uint16_t dataPec = calculatePEC10(pTxBuf, len, false);

    // Append the data PEC to the command buffer
    aCmd[4 + len] = (uint8_t)(dataPec >> ADBMS6948_SHIFT_BY_8);
    aCmd[4 + len + 1] = (uint8_t)(dataPec);

    // Start SPI transaction
    SPI.beginTransaction(settings);
    digitalWrite(TEENSY_SPI_CS, LOW);
    SPI.transfer(aCmd, bufferSize);
    digitalWrite(TEENSY_SPI_CS, HIGH);
    SPI.endTransaction();
}

void readData(uint16_t nCommand, uint8_t *pRxBuf, uint8_t numBytes)
{
    uint16_t nCmdPec;
    // 4 bytes for command, return bytes, 2 bytes for PEC
    uint8_t bytesToRead = numBytes + 2;
    uint8_t bufferSize = 4 + bytesToRead;
    uint8_t aCmd[bufferSize];

    // Populate the command part of the buffer
    aCmd[0] = (uint8_t)((nCommand & 0xFF00u) >> ADBMS6948_SHIFT_BY_8);
    aCmd[1] = (uint8_t)((nCommand & 0x00FFu));

    // Calculate the 15-bit PEC for the command bytes
    nCmdPec = (uint16_t)calculatePEC15(&aCmd[0], 2u);

    // Append the PEC to the command buffer
    aCmd[2] = (uint8_t)(nCmdPec >> ADBMS6948_SHIFT_BY_8);
    aCmd[3] = (uint8_t)(nCmdPec);

    // Fill the rest of the buffer with 0x00
    for (int i = 0; i < bytesToRead; i++)
    {
        aCmd[4 + i] = 0x00; // Uncomment if necessary
    }

    // Start SPI transaction
    SPI.beginTransaction(settings);
    digitalWrite(TEENSY_SPI_CS, LOW);

    // Send the data
    SPI.transfer(aCmd, bufferSize);

    // End SPI transaction
    digitalWrite(TEENSY_SPI_CS, HIGH);
    SPI.endTransaction();

    // Copy the received data to the pRxBuf
    for (int i = 0; i < numBytes; i++)
    {
        pRxBuf[i] = aCmd[4 + i];
    }
}

float convertToVoltage(uint8_t highByte, uint8_t lowByte)
{
    // Combine highByte and lowByte into a uint16_t
    uint16_t twoByteValue = (static_cast<uint16_t>(highByte) << 8) | lowByte;

    // Convert the 2-byte value to voltage
    float voltage = 150e-6 * twoByteValue + 1.5;
    return voltage;
}

void measureVoltages(uint8_t cellVoltageRegisters[])
{
    // Send ADCV (cells) then ADSV (switch) commands
    sendCommand(ADCV);
    delay(3);
    sendCommand(ADSV);

    // Wait for the ADC to finish
    delay(20);

    // Read voltages
    float cellVoltages[18];
    uint8_t n = 0;
    // Read cell voltages
    for (int i = 0; i < 6; i++)
    {
        uint8_t data[6];
        readData(cellVoltageRegisters[i], data, 6);
        // Basic sanity: if all zeros, print a warning once
        if (i == 0 && data[0] == 0 && data[1] == 0 && data[2] == 0 && data[3] == 0 && data[4] == 0 && data[5] == 0)
        {
            Serial.println("WARN: Received all 0s from RDCVx. Check SPI wiring/ISOMD/CS timing.");
        }
        cellVoltages[n] = convertToVoltage(data[1], data[0]);
        cellVoltages[n + 1] = convertToVoltage(data[3], data[2]);
        cellVoltages[n + 2] = convertToVoltage(data[5], data[4]);
        n += 3;
    }

    // Print cell voltages
    for (int i = 0; i < 16; i++)
    {
        Serial.print(cellVoltages[i], 4);
        Serial.print(" ");
    }
    Serial.println();
}

void measureAuxVoltages(uint8_t auxRegisters[])
{
    // Measure command
    sendCommand(ADAX);
    delay(20);

    // Read AUX registers
    float auxVoltages[10];
    uint8_t n = 0;

    for (int i = 0; i < 3; i++)
    {
        uint8_t data[6];
        readData(auxRegisters[i], data, 6);
        auxVoltages[n] = convertToVoltage(data[1], data[0]);
        auxVoltages[n + 1] = convertToVoltage(data[3], data[2]);
        auxVoltages[n + 2] = convertToVoltage(data[5], data[4]);
        n += 3;
    }

    // Print AUX voltages
    Serial.print("AUX:   ");
    for (int i = 0; i < 9; i++)
    {
        Serial.print(auxVoltages[i], 4);
        Serial.print(" ");
    }
    Serial.println();
}

void balanceCells(uint8_t balancePWMs[8], uint8_t timeout)
{
    // Write the balance PWMs
    uint8_t pwma_data[6];
    for (int i = 0; i < 6; i++)
    {
        pwma_data[i] = balancePWMs[i];
    }
    writeData(WRPWMA, pwma_data, 6);

    // put the last 2 bytes into pwmb_data
    uint8_t pwmb_data[6];
    for (int i = 0; i < 2; i++)
    {
        pwmb_data[i] = balancePWMs[i + 6];
    }

    // fill the rest with 0xFF
    for (int i = 2; i < 6; i++)
    {
        pwmb_data[i] = 0xFF;
    }
    writeData(WRPWMB, pwmb_data, 6);

    // Set the balance timeout

    // Read the CFGB register
    uint8_t cfgb_data[6];
    readData(RDCFGB, cfgb_data, 6);

    // Modify the DCTO value, set 4th byte to timeout
    cfgb_data[3] = timeout;
    writeData(WRCFGB, cfgb_data, 6);
}

void setup()
{
    Serial.begin(115200);
    while (!Serial && millis() < 1000)
    {
    }
#if TOGGLE_TEST
    return;
#endif
    SPI.begin();
    pinMode(TEENSY_SPI_CS, OUTPUT);
    digitalWrite(TEENSY_SPI_CS, HIGH);
    pinMode(PIN_ISOMD, OUTPUT);
    digitalWrite(PIN_ISOMD, LOW); // Pull ISOMD low for SPI mode
    Serial.println("Boot: Teensy SPI init, ISOMD=LOW, attempting ID read...");
    wakeup();
    // Try reading silicon ID a few times at boot
    for (int attempt = 0; attempt < 5; ++attempt)
    {
        uint8_t id_buf[2] = {0};
        readData(RDSID, id_buf, 2);
        Serial.print("RDSID[attempt ");
        Serial.print(attempt);
        Serial.print("]: 0x");
        Serial.print(id_buf[0], HEX);
        Serial.print(" ");
        Serial.println(id_buf[1], HEX);
        delay(10);
    }
}

void loop()
{
    // SPI pulse test: force SCK/MOSI activity periodically
    SPI.beginTransaction(settings);
    digitalWrite(TEENSY_SPI_CS, LOW);
    uint8_t pattern[16];
    for (int i = 0; i < 16; ++i)
        pattern[i] = 0xAA; // 1010...
    SPI.transfer(pattern, sizeof(pattern));
    digitalWrite(TEENSY_SPI_CS, HIGH);
    SPI.endTransaction();
    Serial.println("SPI: sent 16 bytes 0xAA");
    delay(500);
}
