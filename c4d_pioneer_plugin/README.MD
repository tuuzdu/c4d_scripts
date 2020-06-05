# Binary file structure

| Field           | Mesurement | Type                      | Offset (B) | Size (B) |
| --------------- | ---------- | ------------------------- | ---------- | -------- |
| Version         |            | uint8_t                   | 0          | 1        |
| AnimationId     |            | uint8_t                   | 1          | 1        |
| FreqPositions   | Hz         | uint8_t                   | 2          | 1        |
| FreqColors      | Hz         | uint8_t                   | 3          | 1        |
| FormatPositions |            | uint8_t                   | 4          | 1        |
| FormatColors    |            | uint8_t                   | 5          | 1        |
| NumberPositions |            | uint16_t                  | 6          | 2        |
| NumberColors    |            | uint16_t                  | 8          | 2        |
| TimeStart       | s          | float                     | 10         | 4        |
| TimeEnd         | s          | float                     | 14         | 4        |
| LatOrigin       | deg        | float                     | 18         | 4        |
| LonOrigin       | deg        | float                     | 22         | 4        |
| AltOrigin       | m          | float                     | 26         | 4        |
| Positions       | m, m, m    | float, float, float       | 100        | 12       |
| Colors          | r, g, b    | uint8_t, uint8_t, uint8_t | 21700      | 3        |