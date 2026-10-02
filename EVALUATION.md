# Evaluation Report — Weather Advisory Support Bot

## 1. Automated evaluation

**Latest test result: 13 passed**

The automated suite covers:
- SOP matching for weather-related activities
- High-wind and no-high-wind paths
- Weather API failure handling
- Paraphrased activity questions
- Adversarial input
- Loading a new SOP without changing Python code
- Session memory for follow-up questions
- No-match behavior

**Result:** All 13 automated tests passed in the latest run.

## 2. Location extraction checks

Tested these question patterns:
- "Would a picnic in Bhopal be suitable today?"
- "Can I go cycling in Bhopal today?"
- "Is running at noon in Indore safe?"
- "Would a picnic in New Delhi be good tomorrow?"

**Expected:** Extract only the city name.

**Observed:** Bhopal, Bhopal, Indore, and New Delhi respectively.

**Result:** Passed.

## 3. Website evaluation

| Case | What was checked | Observed result | Status |
|---|---|---|---|
| Paraphrased cycling: "Would a bike ride be okay in Bhopal today?" | Recognize biking as cycling and use weather data | Returned cycling advisory with wind speed 4.8 km/h and gusts 8.3 km/h. Did not guarantee safety. | Pass with wording limitation |
| Cycling follow-up: "how about biking" | Retain the previous cycling context | Returned a cycling advisory using the previous weather context. | Pass |
| Children at park in Bhopal tomorrow afternoon | Match children-specific park procedures and explain no-match | Returned no-match, but did not show UV or precipitation values explaining why no procedure triggered. | Partial; explanation needs improvement |
| Cycling in Bhopal: "Is it safe to bike to work in Bhopal today?" | Give a transparent response when no cycling SOP triggers | Reported selected-period wind speed and gusts and stated that this does not guarantee safety. | Pass with limitation: exact SOP threshold evidence is not shown |
| Picnic in Bhopal | Extract location from natural wording | Initial attempt failed because "Bhopal be suitable" was treated as the city. Location parsing was corrected and tested separately. | Fixed and verified by location tests |



## 4. Required evaluation cases

### Live severe-weather grounding
**Status: Not verified in the live website evaluation.**

The tested Bhopal cycling response did not show severe wind conditions. A live severe-weather event was not observed during this test, so this case is not marked as passed.

The automated suite includes mocked high-wind behavior. Mocked conditions verify the logic, but do not replace a live severe-weather evaluation.

### No SOP applies
**Status: Partially verified.**

The automated suite includes a no-match case. The website also returned no-match for an indoor book-reading question and for the children-at-park query. The latter did not explain the weather values behind the no-match.

### Weather API unavailable
**Status: Automated test passed.**

The automated suite tests an unreachable weather API and checks that the bot fails honestly rather than inventing weather-based advice.

### Adversarial input
**Status: Automated test passed.**

The automated suite includes an adversarial prompt intended to test whether user instructions can override the written safety procedures.

## 5. Known limitations and next improvements

1. No live severe-weather event was confirmed during website testing.
2. No-match responses should show relevant forecast values and applicable thresholds when available.
3. The cycling no-match response should clearly distinguish forecast values from the exact weather fields checked by the SOP.
4. Some SOP advice is written as internal instructions and needs user-facing wording.
5. Time-only follow-up questions do not consistently retain the earlier activity and location, although some activity-based follow-ups work.
6. Website evaluation is limited to the scenarios recorded above; results may vary with live weather.
