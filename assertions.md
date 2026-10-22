# Assertions

Target: http://127.0.0.1:8767 at commit 64b7c342ec5797660239dfc83d5dc4e4fafe427a, Chromium as Pixel 7

setup: Fresh data file with the three sample dishes at http://127.0.0.1:8767

- passed: Precondition: the shopping list is empty (`01-precondition-list-empty-passed.png`)

## It should rescale a dish when the servings change

- passed: Curry for 2: 1 Stk Süßkartoffel, 200 ml Kokosmilch (`02-curry-for-2-servings-passed.png`)

## It should put the scaled ingredients on the list

- passed: 7 curry items listed, Zwiebel 0,5 Stk für Gemüsecurry (`03-curry-on-the-list-passed.png`)

## It should merge an ingredient that two dishes need

- passed: One Zwiebel row: 1,5 Stk, for both dishes; 13 items (`04-onion-merged-passed.png`)

## It should tick items off and clear them

- passed: After clearing: 11 open items, no Zwiebel row (`05-ticked-items-cleared-passed.png`)
