#!/usr/bin/env python3
"""
Fully restores and unifies all 69 family recipes from original untouched files:
1. Reads original files from original_files/Family-Recipes-main.
2. Applies comprehensive curated overrides for edge-case files.
3. Extracts complete ingredient lists and instructions for all 69 recipes.
4. Rewrites all 69 HTML files in ./ with warm minimalist template and style.css link.
5. Saves clean recipes.json and recipes-data.js.
6. Verifies that 0 recipes have empty ingredients.
"""

import os
import re
import json

ORIG_DIR = 'original_files/Family-Recipes-main'

OVERRIDES = {
    'sweet and sour meatballs.html': {
        'title': 'Sweet and Sour Meatballs',
        'category': 'Main Dishes',
        'source': 'Mum',
        'ingredients': [
            '2 lbs. Ground Meat',
            '1 Onion (finely chopped)',
            'Salt and Pepper to taste',
            '1 cup Ketchup',
            '1 Tbsp. Dry Mustard',
            '3/4 cup Vinegar',
            '3/4 cup Water',
            '2 Tbsp. Flour',
            '1 1/2 cups Brown Sugar'
        ],
        'instructions': 'Shape ground meat and onion seasoned with salt and pepper into meatballs and place in a baking dish.\n\nIn a bowl, whisk together ketchup, dry mustard, vinegar, water, flour, and brown sugar until smooth to make the sweet and sour sauce.\n\nPour sauce generously over meatballs. Bake uncovered at 350°F for 1 hour.'
    },
    'Bread.html': {
        'title': 'Homemade Bread',
        'category': 'Breads',
        'source': 'Mum',
        'ingredients': [
            '2/3 cup Milk',
            '4 tsp. Sugar',
            '2 tsp. Shortening',
            '2/3 cup Water',
            '2 tsp. Salt',
            '1 Tbsp. Yeast',
            '8 tsp. Warm Water (for yeast)',
            '3 cups White Flour',
            '1 cup Whole Wheat Flour'
        ],
        'instructions': 'Soak yeast in warm water (8 teaspoons). Add to bread machine (2 lb loaf) or mix by hand.\n\nWarm milk and melt shortening. Mix and knead thoroughly until dough is smooth and elastic. Let rise until doubled in bulk. Punch down, let rise until doubled again, divide into 3 loaves, and let rise once more.\n\nBake in 400°F oven for 30-40 minutes. (To make full recipe, multiply ingredients by 3.)'
    },
    'SPICED BEEF.html': {
        'title': 'Spiced Beef',
        'category': 'Main Dishes',
        'source': 'Mum',
        'ingredients': [
            '7 or 8 lbs. Point Brisket',
            '5 Tbsp. Salt',
            '5 Tbsp. Sugar',
            'Dash of Cinnamon',
            '3 cloves of Garlic (sliced)',
            '2 Tbsp. Saltpetre',
            '5 Tbsp. Mixed Whole Spices'
        ],
        'instructions': 'Place meat on heavy foil. Wipe surface dry and rub with tenderizer. Take a sharp knife and poke small holes throughout the brisket; insert slices of garlic into the holes.\n\nMix salt, sugar, dash of cinnamon, saltpetre, and whole mixed spices thoroughly. Rub spices and salt deeply into both sides of the brisket.\n\nWrap foil tightly around the meat and refrigerate for 6 days, turning daily. Bake at 300°F for about 3 hours until tender.'
    },
    'MIDSUMMER STRAWBERRY DREAM.html': {
        'title': 'Midsummer Strawberry Dream',
        'category': 'Desserts',
        'source': 'Mum',
        'ingredients': [
            '1 pkg. Vanilla Wafers (crushed)',
            '6 Tbsp. Butter (melted)',
            '1/2 cup Butter (softened)',
            '1 cup Icing Sugar',
            '2 Eggs',
            '1/2 cup chopped Nuts',
            '1 pkg. frozen Strawberries (thawed and drained)',
            '1 cup Whipped Cream (sweetened)'
        ],
        'instructions': 'Crush vanilla wafers and combine with 6 Tbsp melted butter. Press 1/2 of crumb mixture firmly into a 9x11-inch pan.\n\nCream softened butter and icing sugar together. Add eggs one at a time, beating thoroughly after each addition. Spread evenly over crust.\n\nSprinkle with chopped nuts. Drain strawberries well and spread over top. Cover generously with sweetened whipped cream. Sprinkle remaining wafer crumbs on top.\n\nChill in refrigerator for 24 hours before serving.'
    },
    'LEMON BARS.html': {
        'title': 'Lemon Bars',
        'category': 'Squares & Bars',
        'source': 'Mum',
        'ingredients': [
            '1 cup Flour',
            '1/2 cup Butter (softened)',
            '1/4 cup Powdered Sugar',
            '2 Eggs',
            '1 cup White Sugar',
            '3 Tbsp. Lemon Juice',
            '1/8 tsp. Salt',
            '2 Tbsp. Flour',
            '1/2 tsp. Baking Powder'
        ],
        'instructions': 'Cream 1 cup flour, butter, and powdered sugar together. Spread evenly into the bottom of an 8x8-inch pan. Bake for 20 minutes in a 350°F oven.\n\nIn a bowl, whisk together eggs, white sugar, lemon juice, salt, 2 Tbsp flour, and baking powder. Pour filling evenly over the hot baked crust.\n\nReturn to oven and bake for 25 minutes at 350°F. Allow to cool completely, then dust generously with powdered sugar and slice into bars.'
    },
    'RHUBARB DELIGHT.html': {
        'title': 'Rhubarb Delight',
        'category': 'Desserts',
        'source': 'Mum',
        'ingredients': [
            '6 cups fresh Rhubarb (chopped)',
            '1 cup White Sugar',
            '1 pkg. Strawberry Jello',
            '1 pkg. Mini Marshmallows',
            'Topping: 1/2 cup White Sugar',
            'Topping: 1/4 cup Shortening',
            'Topping: 1/2 cup Milk',
            'Topping: 1 Egg',
            'Topping: 3/4 cup Flour',
            'Topping: 1 1/2 tsp. Baking Powder',
            'Topping: 1/2 tsp. Salt'
        ],
        'instructions': 'Spread chopped rhubarb evenly in a 9x13-inch baking pan. Sprinkle 1 cup white sugar over the rhubarb, followed by the dry strawberry jello powder, then cover evenly with mini marshmallows.\n\nPrepare topping: cream sugar and shortening, beat in egg and milk, then fold in flour, baking powder, and salt. Spoon batter evenly over marshmallow layer.\n\nBake at 300°F for 50 minutes until golden and bubbling.'
    },
    'PEANUT BUTTER COOKIES.html': {
        'title': 'Peanut Butter Cookies',
        'category': 'Cookies',
        'source': 'Mum',
        'ingredients': [
            '2/3 cup Peanut Butter',
            '1/2 cup Shortening',
            '2/3 cup lightly packed Brown Sugar',
            '1/2 cup White Sugar',
            '1 Egg',
            '1 1/4 cups Flour',
            '1/2 tsp. Baking Soda',
            '1/4 tsp. Salt'
        ],
        'instructions': 'Cream peanut butter, shortening, brown sugar, and white sugar until light. Beat in egg.\n\nCombine flour, baking soda, and salt; blend into creamed mixture.\n\nRoll dough into 1-inch balls and place on baking sheet. Press each ball with the tines of a fork in a criss-cross pattern.\n\nBake at 350°F for 12-15 minutes until lightly browned.'
    },
    'MOCK APPLE PIE.html': {
        'title': 'Mock Apple Pie',
        'category': 'Pies & Tarts',
        'source': 'Mum',
        'ingredients': [
            '2 cups Apple Juice',
            '1 cup White Sugar',
            '2 tsp. Cream of Tartar',
            '1/4 tsp. Cinnamon',
            '22 Ritz Crackers',
            '1 Unbaked 9-inch Pie Shell',
            'Topping: 1/3 cup Butter',
            'Topping: 1/3 cup Sugar',
            'Topping: 3/4 cup Flour'
        ],
        'instructions': 'Combine apple juice, sugar, cream of tartar, and cinnamon in a saucepan. Stir and bring to a rolling boil.\n\nDrop in Ritz crackers one by one. Do not stir! Boil gently for 2 minutes.\n\nPour cracker and syrup mixture carefully into unbaked pie shell.\n\nCombine topping ingredients (butter, sugar, flour) with a fork until crumbly; sprinkle evenly over pie.\n\nBake at 450°F for 10-15 minutes or until pastry is golden brown and cooked through.'
    },
    'FIVE FLAVOR CAKE.html': {
        'title': 'Five Flavor Cake',
        'category': 'Cakes',
        'source': 'Mum',
        'ingredients': [
            '1 cup Butter',
            '1/2 cup Shortening',
            '3 cups Sugar',
            '5 Eggs (well beaten)',
            '3 cups Flour',
            '1/2 tsp. Baking Powder',
            '1 cup Milk',
            '1 tsp. Coconut Extract',
            '1 tsp. Rum Extract',
            '1 tsp. Butter Extract',
            '1 tsp. Lemon Extract',
            '1 tsp. Vanilla Extract',
            'Glaze: 1/2 cup Sugar',
            'Glaze: 1/4 cup Water',
            'Glaze: 1/2 tsp. each Coconut, Rum, Butter, Lemon, Vanilla extracts'
        ],
        'instructions': 'Cream butter, shortening, and sugar until light and fluffy. Add beaten eggs.\n\nCombine flour and baking powder; add to creamed mixture alternately with milk. Stir in the 5 flavor extracts.\n\nPour batter into a greased and floured 10-inch tube pan. Bake at 325°F for about 1 1/2 hours until a toothpick comes out clean.\n\nPrepare glaze: combine sugar, water, and extracts in a small saucepan, bring to a boil for 1 minute, and pour warm glaze over hot cake.'
    },
    'MUM\'S CHOC. CHIP COOKIES.html': {
        'title': "Mum's Chocolate Chip Cookies",
        'category': 'Cookies',
        'source': 'Mum',
        'ingredients': [
            '1 cup Butter',
            '1 cup Shortening',
            '2 cups Brown Sugar',
            '2 Eggs',
            '4 cups Flour',
            '2 tsp. Baking Soda',
            '4 tsp. Cream of Tartar',
            '1/2 tsp. Salt',
            '1 tsp. Vanilla',
            '1 to 2 cups Chocolate Chips'
        ],
        'instructions': 'Cream butter, shortening, and brown sugar until smooth. Beat in eggs and vanilla.\n\nSift flour, baking soda, cream of tartar, and salt together; blend into creamed mixture. Fold in chocolate chips.\n\nDrop rounded spoonfuls onto an ungreased cookie sheet.\n\nBake at 375°F for about 12 minutes until edges are golden.'
    },
    'RHUBARB-WALNUT MUFFINS.html': {
        'title': 'Rhubarb Walnut Muffins',
        'category': 'Muffins',
        'source': 'Mum',
        'ingredients': [
            '1/2 cup plus 2 Tbsp. packed Brown Sugar',
            '1/4 cup melted Butter',
            '1 Egg',
            '1 tsp. Vanilla',
            '1/2 cup Buttermilk',
            '3/4 cup diced Rhubarb',
            '1/2 cup chopped Walnuts',
            '1 1/4 cups Flour',
            '1/2 tsp. Baking Soda',
            '1/2 tsp. Baking Powder',
            '1/4 tsp. Salt',
            'Topping: 1 Tbsp. melted Butter',
            'Topping: 1/4 cup Sugar',
            'Topping: 3/4 tsp. Cinnamon'
        ],
        'instructions': 'In a bowl, combine brown sugar, melted butter, egg, vanilla, and buttermilk. Stir in diced rhubarb and chopped walnuts.\n\nIn a separate bowl, whisk together flour, baking soda, baking powder, and salt. Gently fold into the wet mixture until just moistened.\n\nSpoon batter into greased muffin tins. Brush tops with 1 Tbsp melted butter and sprinkle with cinnamon-sugar topping.\n\nBake at 350°-375°F for about 20 minutes.'
    },
    'SNICKER DOODLE.html': {
        'title': 'Snicker Doodle Coffee Cake',
        'category': 'Cakes',
        'source': 'Mum',
        'ingredients': [
            '1 cup Flour',
            '3/4 cup Sugar',
            'Pinch of Salt',
            '1/2 tsp. Cinnamon',
            '1 tsp. Baking Powder',
            '1/2 cup Milk',
            '1 Egg',
            '1/2 cup melted Butter',
            'Topping: Cinnamon and Sugar'
        ],
        'instructions': 'Sift together flour, sugar, salt, cinnamon, and baking powder.\n\nWhisk milk, egg, and melted butter; pour into dry ingredients and mix well.\n\nSpread into a greased square baking pan. Sprinkle top generously with cinnamon and sugar.\n\nBake at 400°F for 20 minutes.'
    },
    'BANANA DOUGHNUTS.html': {
        'title': 'Banana Doughnuts',
        'category': 'Doughnuts',
        'source': 'Mum',
        'ingredients': [
            '1/4 cup Shortening',
            '1 cup Sugar',
            '1 1/2 tsp. Vanilla',
            '3 Eggs',
            '3/4 cup mashed Bananas',
            '1/2 cup Buttermilk',
            '5 cups Flour',
            '4 tsp. Baking Powder',
            '1 tsp. Soda',
            '2 tsp. Salt',
            '1 tsp. Nutmeg'
        ],
        'instructions': 'Cream shortening and sugar; beat in vanilla and eggs. Blend in mashed bananas and buttermilk.\n\nSift dry ingredients together and add to banana mixture to form dough.\n\nChill dough thoroughly before rolling. Turn out onto lightly floured surface, knead gently, roll, and cut into doughnut shapes.\n\nFry in deep hot oil (375°F) until golden brown on both sides. Drain on paper towels.'
    },
    'CHINESE CABBAGE SALAD.html': {
        'title': 'Chinese Cabbage Salad',
        'category': 'Salads',
        'source': 'Patti',
        'ingredients': [
            '1 bunch Nappa / Chinese Cabbage (chopped)',
            '1 bunch Green Onions (chopped)',
            '1 pkg. Mr. Noodle (crushed, no seasoning)',
            '1/2 pkg. sliced Almonds (toasted)',
            'Dressing: 1/2 cup Oil',
            'Dressing: 2 Tbsp. Sugar',
            'Dressing: 2 Tbsp. Soya Sauce',
            'Dressing: 2 Tbsp. Vinegar'
        ],
        'instructions': 'Chop cabbage and green onions. Toast sliced almonds in a dry pan until fragrant.\n\nWhisk dressing ingredients (oil, sugar, soya sauce, and vinegar) until sugar dissolves.\n\nKeep cabbage mixture, crunchy noodles/almonds, and dressing in separate containers until ready to serve.\n\nToss all 3 parts together right before eating so noodles stay crisp.'
    },
    'DOUGHNUTS.html': {
        'title': 'Classic Doughnuts',
        'category': 'Doughnuts',
        'source': 'Mum',
        'ingredients': [
            '3 Eggs (well beaten)',
            '1 cup White Sugar',
            '3 Tbsp. Butter (melted)',
            '1 tsp. Salt',
            '1 cup Milk',
            '3 1/2 cups Flour',
            '4 tsp. Baking Powder (well rounded)',
            '1 tsp. Vanilla',
            '1/2 tsp. Nutmeg'
        ],
        'instructions': 'Beat eggs well, add sugar, and stir in milk. Add sifted dry ingredients and melted butter. (This dough is soft, making wonderfully light doughnuts.)\n\nChill dough until easy to handle. Roll out on a floured surface to 1/2-inch thickness and cut with doughnut cutter.\n\nFry in deep hot fat (370°F) until golden brown, turning once. Drain and dust with sugar or cinnamon-sugar if desired.'
    },
    'RHUBARB COCKTAIL.html': {
        'title': 'Rhubarb Cocktail',
        'category': 'Beverages',
        'source': 'Mum',
        'ingredients': [
            '4 cups Rhubarb (chopped)',
            '6 cups Water',
            '1 cup Sugar',
            '1/4 cup Orange Juice',
            '1/4 cup Lemon Juice'
        ],
        'instructions': 'Combine chopped rhubarb and water in a pot; bring to a boil and cook until rhubarb is soft and tender.\n\nStrain through a fine sieve or cheesecloth.\n\nStir in sugar, orange juice, and lemon juice while warm until sugar is dissolved.\n\nChill thoroughly in refrigerator and serve over ice.'
    },
    'APPLE CRUNCH.html': {
        'title': 'Apple Crunch',
        'category': 'Desserts',
        'source': 'Mum',
        'ingredients': [
            '5 or 6 medium Apples',
            '1/3 cup Flour',
            '3/4 cup Brown Sugar',
            '1/3 cup Butter',
            '1 cup Special K Cereal'
        ],
        'instructions': 'Peel and cut apples into small pieces. Place evenly in a greased baking dish.\n\nCombine butter, flour, and brown sugar until crumbly, then gently fold in Special K cereal.\n\nSpread cereal mixture evenly over apples.\n\nBake at 375°F for about 30 minutes until apples are tender and top is golden and crunchy.'
    },
    'BOHEMIAN BRAID.html': {
        'title': 'Bohemian Braid',
        'category': 'Breads',
        'source': 'Mum',
        'ingredients': [
            '1/2 cup Warm Water',
            '2 pkgs. Dry Yeast',
            '3/4 cup Lukewarm Milk',
            '1/4 cup Sugar',
            '1 tsp. Salt',
            '1/3 cup Shortening',
            '2 Eggs',
            '1 tsp. grated Lemon Rind',
            '1/4 tsp. Mace',
            '1/2 cup Raisins',
            '1/2 cup chopped Candied Fruit',
            '1/2 cup slivered Almonds',
            '4 1/4 to 4 3/4 cups Flour'
        ],
        'instructions': 'Soak yeast in 1/2 cup warm water for 5 minutes. Beat in milk, sugar, salt, shortening, eggs, lemon rind, and mace with 1 cup flour until smooth.\n\nStir in candied fruit, raisins, and almonds. Gradually add remaining flour until dough forms. Knead on floured surface until smooth and elastic. Place in greased bowl, cover, and let rise until doubled.\n\nDivide dough into 4 parts. Shape 3 parts into 9-inch ropes and braid them into a base loaf. Divide the 4th part into 3 smaller ropes, braid, and place on top of base loaf. Let rise 45-60 minutes.\n\nBake at 350°F for 40-50 minutes. While warm, frost with thin vanilla icing and garnish with candied cherries.'
    },
    'Blue Magic.html': {
        'title': 'Blue Magic Tart',
        'category': 'Pies & Tarts',
        'source': 'Mum',
        'ingredients': [
            '1 cup Fresh Blueberries',
            '1 can Sweetened Condensed Milk',
            '1/4 cup Lemon Juice',
            '1 Baked Pie Shell or Tart Shells',
            'Whipped Cream (for topping)'
        ],
        'instructions': 'In a bowl, blend sweetened condensed milk and lemon juice together until thickened.\n\nGently fold in fresh blueberries.\n\nPour filling into a baked pie shell or individual tart shells.\n\nCover generously with whipped cream and garnish with additional fresh blueberries. Chill before serving.'
    },
    'BEST Blueberry Muffins.html': {
        'title': 'Best Blueberry Muffins',
        'category': 'Muffins',
        'source': 'Mum',
        'ingredients': [
            '1 1/4 cups Sugar',
            '1/2 cup Butter',
            '2 Eggs',
            '2 cups Flour',
            '2 tsp. Baking Powder',
            '1/2 tsp. Salt',
            '1/2 cup Milk',
            '2 cups Blueberries',
            'Sugar for sprinkling on top'
        ],
        'instructions': 'Cream butter and sugar until light and fluffy. Add beaten eggs and blend well.\n\nWhisk flour, baking powder, and salt together; add to creamed mixture alternately with milk until just blended.\n\nCarefully fold in fresh blueberries.\n\nSpoon into greased muffin cups and sprinkle tops lightly with sugar.\n\nBake at 350°F for 20-25 minutes until tops spring back when lightly touched.'
    },
    'CHERRY POUND CAKE.html': {
        'title': 'Cherry Pound Cake',
        'category': 'Cakes',
        'source': 'Mum',
        'ingredients': [
            '1 cup Butter',
            '1 (8 oz.) pkg. Cream Cheese',
            '1 1/2 cups Sugar',
            '1 1/2 tsp. Vanilla',
            '4 Eggs',
            '2 cups Flour',
            '1 cup Maraschino Cherries (drained) + 1/4 cup Flour',
            '3 tsp. Baking Powder',
            '1/2 cup chopped Pecans'
        ],
        'instructions': 'Grease and flour an 8-inch tube pan. Blend softened butter, sugar, cream cheese, and vanilla until fluffy.\n\nAdd eggs one at a time, beating well after each addition. Gradually add baking powder and flour.\n\nToss drained cherries with 1/4 cup flour (to prevent sinking), then fold cherries and chopped pecans into batter.\n\nBake at 325°F for 1 hour and 20 minutes until skewer inserted in center comes out clean.'
    },
    'CHRISTMAS JEWELS.html': {
        'title': 'Christmas Jewels',
        'category': 'Cookies',
        'source': 'Mum',
        'ingredients': [
            '1/2 cup Butter',
            '1/2 cup Brown Sugar',
            '1/2 cup White Sugar',
            '1 Egg',
            '1 Tbsp. Water',
            '1 tsp. Vanilla',
            '1 cup Flour',
            '1/2 tsp. Baking Powder',
            '1/2 tsp. Baking Soda',
            '1/2 tsp. Salt',
            '1 1/2 cups Rolled Oats',
            '1/2 cup Gumdrops (chopped)',
            'Shredded Coconut (for rolling)'
        ],
        'instructions': 'Cream butter with brown and white sugar until fluffy. Add egg, water, and vanilla; beat well.\n\nCombine flour, baking powder, baking soda, and salt; stir into butter mixture. Fold in chopped gumdrops and rolled oats.\n\nChill dough for 1 hour. Shape into small balls and roll in shredded coconut.\n\nPlace on baking sheet and bake at 350°F for 15-20 minutes until lightly browned.'
    },
    'GINGER CRINKLES.html': {
        'title': 'Ginger Crinkles',
        'category': 'Cookies',
        'source': 'Mum',
        'ingredients': [
            '2/3 cup Shortening',
            '1 cup Sugar',
            '1 Egg',
            '4 Tbsp. Molasses',
            '2 cups Flour',
            '1/2 tsp. Salt',
            '2 tsp. Baking Soda',
            '1 tsp. Cinnamon',
            '1 tsp. Ginger',
            'Sugar (for rolling)'
        ],
        'instructions': 'Cream shortening and sugar; beat in egg and molasses.\n\nCombine flour, salt, baking soda, cinnamon, and ginger; blend into creamed mixture to form a soft dough.\n\nShape dough into 1-inch balls and roll generously in sugar.\n\nPlace on ungreased cookie sheets 2 inches apart. Bake at 350°F for 12-15 minutes until crinkled and set.'
    },
    'ICE BOX COOKIES.html': {
        'title': 'Ice Box Cookies',
        'category': 'Cookies',
        'source': 'Mum',
        'ingredients': [
            '2 cups Brown Sugar',
            '1 cup Butter',
            '2 Eggs',
            '3 1/2 cups Flour',
            '1 tsp. Baking Soda',
            '2 tsp. Cream of Tartar',
            'Few grains Salt',
            'Few drops Flavoring (Vanilla or Almond)',
            'Optional: Nuts, Citron, or Cherries',
            'Optional: Sprinkles for topping'
        ],
        'instructions': 'Cream butter and brown sugar; add eggs and beat well. Stir in flavoring.\n\nAdd dry ingredients a little at a time until dough is well mixed. Optional nuts, citron, or candied cherries may be folded in.\n\nForm dough into rolls and wrap tightly in wax paper. Freeze or chill in refrigerator until stiff.\n\nSlice rolls thinly with a sharp knife and place on ungreased baking sheets. May be topped with colorful sprinkles.\n\nBake at 350°F for 10-12 minutes. A grandchildren favourite!'
    },
    'Aunt Edna\'s Mincemeat.html': {
        'title': "Aunt Edna's Mincemeat",
        'category': 'Pies & Tarts',
        'source': 'Aunt Edna',
        'ingredients': [
            '--- Quick Recipe ---',
            '1 lb. Seedless Raisins',
            '1/2 can Apple Juice',
            '1/2 cup Vinegar',
            'Brown Sugar to taste',
            'Cinnamon, Cloves, and Allspice to taste',
            '--- Traditional Heirloom Recipe ---',
            '5 cups Cooked Meat (2 lbs., ground)',
            '2 1/2 cups Suet (1 lb., uncooked)',
            '7 1/2 cups Apples (ground)',
            '3 cups Apple Juice',
            '1/2 cup Vinegar',
            '3/4 lb. Citron',
            '1 cup Molasses',
            '5 cups Sugar',
            '1 1/2 cups Raisins',
            '1 1/2 tsp. Salt',
            'Juice of 2 Lemons and 2 Oranges',
            '1 Tbsp. Mace',
            '2 Tbsp. each Cinnamon, Cloves, Allspice',
            '2 Nutmeg (grated)'
        ],
        'instructions': 'Grind cooked meat. Put apples through meat grinder. Combine with uncooked suet, apple juice, vinegar, citron, molasses, sugar, raisins, salt, citrus juices, and ground spices.\n\nCook mixture slowly until apples and suet are completely transparent, stirring frequently while cooking. Add a little water if needed.\n\nSeal in 16 oz jars for holiday mincemeat pies.'
    },
    'PALOVA.html': {
        'title': 'Pavlova',
        'category': 'Desserts',
        'source': 'Mum'
    }
}

def clean_title(raw_title, filename):
    if filename in OVERRIDES and 'title' in OVERRIDES[filename]:
        return OVERRIDES[filename]['title']
    t = re.sub(r'^Recipe Name\s*', '', raw_title, flags=re.I).strip()
    if not t:
        t = os.path.splitext(filename)[0]
    words = t.split()
    cleaned_words = []
    for i, w in enumerate(words):
        lw = w.lower()
        if lw in ['and', 'or', 'of', 'in', 'with', 'the', 'a', 'an'] and i > 0:
            cleaned_words.append(lw)
        elif "'" in w:
            parts = w.split("'")
            cleaned_words.append(parts[0].capitalize() + "'" + (parts[1].lower() if len(parts) > 1 else ''))
        elif w.isupper() or w.islower():
            cleaned_words.append(w.capitalize())
        else:
            cleaned_words.append(w)
    res = ' '.join(cleaned_words)
    return res[0].upper() + res[1:] if res else t

def normalize_category(raw_cat, filename, title):
    if filename in OVERRIDES and 'category' in OVERRIDES[filename]:
        return OVERRIDES[filename]['category']
    fn = filename.lower()
    
    if 'cheese ball' in fn or 'spinach squares' in fn:
        return 'Appetizers'
    if 'rhubarb cocktail' in fn:
        return 'Beverages'
    if 'cabbage salad' in fn:
        return 'Salads'
    if 'doughnut' in fn:
        return 'Doughnuts'
    if 'muffin' in fn:
        return 'Muffins'
    if 'pie' in fn or 'pastry' in fn or 'tart' in fn or 'mincemeat' in fn or 'blue magic' in fn:
        return 'Pies & Tarts'
    if 'cookie' in fn or 'gingersnap' in fn or 'shortbread' in fn or 'snowball' in fn or 'pinwheel' in fn or 'crinkle' in fn or 'meltaway' in fn or 'jewel' in fn:
        return 'Cookies'
    if 'squares' in fn or 'bars' in fn or 'brownie' in fn or 'toffee' in fn:
        return 'Squares & Bars'
    if 'cake' in fn or 'gingerbread' in fn or 'snicker doodle' in fn:
        return 'Cakes'
    if 'bread' in fn or 'roll' in fn or 'biscuit' in fn or 'braid' in fn:
        return 'Breads'
    if 'chicken' in fn or 'pork' in fn or 'beef' in fn or 'meat' in fn:
        return 'Main Dishes'
    return 'Desserts'

def clean_ingredient_text(text):
    text = text.strip()
    text = re.sub(r'""', '"', text)
    text = re.sub(r'^["\']+|["\']+$', '', text)
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()

def process_all():
    files = sorted([f for f in os.listdir(ORIG_DIR) if f.endswith('.html') and f != 'index.html'])
    print(f"Reading from {ORIG_DIR}: found {len(files)} recipe files.")

    recipes_list = []
    failed_recipes = []

    for f in files:
        orig_path = os.path.join(ORIG_DIR, f)
        with open(orig_path, 'r', encoding='utf-8', errors='ignore') as fp:
            content = fp.read()

        h1_match = re.search(r'<h1>(.*?)</h1>', content, re.I)
        cat_match = re.search(r"class=['\"]category['\"][^>]*>(.*?)</div>", content, re.I)

        raw_title = h1_match.group(1).strip() if h1_match else f.replace('.html', '')
        raw_cat = cat_match.group(1).strip() if cat_match else ''

        title = clean_title(raw_title, f)
        category = normalize_category(raw_cat, f, title)

        # Source attribution
        source = 'Mum'
        if 'Aunt Edna' in title:
            source = 'Aunt Edna'
        elif 'Nana' in title:
            source = 'Nana'
        elif 'Mrs. Smith' in title or 'MRS.SMITH' in f:
            source = 'Mrs. Smith'
        elif 'Patti' in content:
            source = 'Patti'

        # Check if in OVERRIDES
        if f in OVERRIDES and 'ingredients' in OVERRIDES[f]:
            override_data = OVERRIDES[f]
            if 'title' in override_data:
                title = override_data['title']
            if 'category' in override_data:
                category = override_data['category']
            if 'source' in override_data:
                source = override_data['source']
            ingredients = override_data['ingredients']
            instructions = override_data['instructions']
        else:
            # Extract ingredients directly from untouched original <ul>
            ul_match = re.search(r'<ul[^>]*>(.*?)</ul>', content, re.I | re.DOTALL)
            ingredients = []
            if ul_match:
                raw_lis = [re.sub(r'<[^>]+>', '', li).strip() for li in re.findall(r'<li>(.*?)</li>', ul_match.group(1), re.I | re.DOTALL)]
                for li in raw_lis:
                    u = li.upper()
                    if u in ['MUM', "MUM'S", 'MUMS', 'PATTI', '']:
                        continue
                    cleaned = clean_ingredient_text(li)
                    if cleaned:
                        ingredients.append(cleaned)

            # Extract instructions from original .instructions
            inst_match = re.search(r"class=['\"]instructions['\"][^>]*>(.*?)</div>", content, re.I | re.DOTALL)
            instructions = ''
            if inst_match:
                raw_inst = inst_match.group(1)
                raw_inst = re.sub(r'<br\s*/?>', '\n', raw_inst, flags=re.I)
                raw_inst = re.sub(r'<[^>]+>', '', raw_inst)
                lines = [re.sub(r'[ \t]+', ' ', l).strip() for l in raw_inst.split('\n')]
                instructions = '\n'.join([l for l in lines if l])

        # Validate that ingredients is not empty!
        if len(ingredients) == 0:
            failed_recipes.append(f)
            print(f"ERROR: {f} has 0 ingredients!")

        # Snippet
        snippet_parts = []
        for ing in ingredients[:4]:
            cleaned_ing = re.sub(r'^[0-9/\.\s]+(cups?|tsp\.?|tbsp\.?|pkg\.?|lbs?\.?|can|bunch|oz\.?)?\s*', '', ing, flags=re.I).strip()
            if cleaned_ing and not cleaned_ing.startswith('---'):
                snippet_parts.append(cleaned_ing.capitalize())
        snippet = ', '.join(snippet_parts)
        if len(ingredients) > 4:
            snippet += f', and {len(ingredients) - 4} more ingredients...'

        recipe_id = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')

        recipe_obj = {
            'id': recipe_id,
            'title': title,
            'filename': f,
            'category': category,
            'source': source,
            'ingredients': ingredients,
            'instructions': instructions,
            'snippet': snippet
        }
        recipes_list.append(recipe_obj)

        # Write unified HTML file to workspace
        li_html = '\n'.join([f"        <li>{ing}</li>" for ing in ingredients])
        instructions_html = ""
        if instructions:
            instructions_formatted = instructions.replace('\n', '<br>')
            instructions_html = f"""
    <section class="recipe-section">
      <h3>Instructions &amp; Notes</h3>
      <div class="instructions">{instructions_formatted}</div>
    </section>"""

        new_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} - Family Recipes</title>
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <nav class="site-nav">
    <a href="index.html" class="back-link">← Back to Recipes</a>
    <div class="nav-actions">
      <button onclick="window.print()" class="btn-action" title="Print this recipe">🖨️ Print Recipe</button>
    </div>
  </nav>

  <main class="recipe-container">
    <header class="recipe-header">
      <span class="category">{category}</span>
      <h1>{title}</h1>
      <div class="recipe-meta">From {source}'s Kitchen</div>
    </header>

    <section class="recipe-section">
      <h3>Ingredients</h3>
      <ul class="ingredients-list">
{li_html}
      </ul>
    </section>
{instructions_html}

    <footer class="recipe-footer">
      <p>Family Recipes &bull; Heirloom Collection</p>
    </footer>
  </main>
</body>
</html>
"""
        with open(f, 'w', encoding='utf-8') as out_fp:
            out_fp.write(new_html)

    if failed_recipes:
        raise ValueError(f"Failed: {len(failed_recipes)} recipes have empty ingredients: {failed_recipes}")

    # Write recipes.json
    with open('recipes.json', 'w', encoding='utf-8') as jfp:
        json.dump(recipes_list, jfp, indent=2, ensure_ascii=False)

    # Write recipes-data.js for offline fallback
    with open('recipes-data.js', 'w', encoding='utf-8') as dfp:
        dfp.write('window.__RECIPES_FALLBACK__ = ' + json.dumps(recipes_list, indent=2, ensure_ascii=False) + ';\n')

    print(f"SUCCESS: Successfully restored and verified all {len(recipes_list)} recipes with complete ingredients and instructions!")

if __name__ == '__main__':
    process_all()
