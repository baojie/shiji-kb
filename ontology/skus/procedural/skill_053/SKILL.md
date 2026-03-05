---
name: three-division-tuning-method
description: Use when calculating musical note frequencies and pipe lengths for the five-tone scale in traditional Chinese music theory.
---

# Three Division Tuning Method (三分损益法)

This ancient Chinese method calculates the lengths of musical pipes for the pentatonic scale (宫商角徵羽 - Gong, Shang, Jue, Zhi, Yu).

## Overview
The method uses alternating division by 3 to generate successive notes, creating a mathematical relationship between pipe lengths.

## Base Values
- Start with 81 (九九八十一) as the base unit for 宫

## Calculation Steps

1. **Calculate 徵**
   - Take 宫 value: 81
   - Divide by 3, subtract 1/3: 81 × (2/3) = 54
   - Result: 徵 = 54

2. **Calculate 商**
   - Take 徵 value: 54
   - Divide by 3, add 1/3: 54 × (4/3) = 72
   - Result: 商 = 72

3. **Calculate 羽**
   - Take 商 value: 72
   - Divide by 3, subtract 1/3: 72 × (2/3) = 48
   - Result: 羽 = 48

4. **Calculate 角**
   - Take 羽 value: 48
   - Divide by 3, add 1/3: 48 × (4/3) = 64
   - Result: 角 = 64

## Final Scale Lengths
| Note | Length | Relationship |
|------|--------|--------------|
| 宫 | 81 | Base |
| 商 | 72 | 宫 × 8/9 |
| 角 | 64 | 宫 × 64/81 |
| 徵 | 54 | 宫 × 2/3 |
| 羽 | 48 | 宫 × 16/27 |

## Principle
- "下生" (descending generation): multiply by 2/3
- "上生" (ascending generation): multiply by 4/3
- Alternating creates the pentatonic scale
