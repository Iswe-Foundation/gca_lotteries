# Global Citizens' Assembly Location Lottery System

## Overview

This code implements a **population-weighted random lottery system** for selecting the geographic locations of Assembly Members for the Global Citizens' Assembly's (GCA) Civic Assembly. It is based on [the lottery selection code from the 2021 Global Assembly](https://github.com/GlobalAssembly/global-select-app/blob/main/global-select-admin-centroids.py). The system ensures that each person worldwide has an **equal probability** of having their location selected, while simultaneously enforcing multiple quota systems to ensure geographic, demographic, and climate-risk diversity.

## Purpose

The primary goal is to select 105 locations (this number can be changed) worldwide that:

* Give each individual person an equal chance of selection (population-weighted), subject to the following constraints:
  * No UN Region should have more than its share of the global population
  * No country should have more than its share of the global population
  * No climate risk band should have more than its share of the global population (details explained below)
* Optionally, promote diversity to ensure a minimum number of countries are included
* Optionally, guarantee inclusion of a specified proportion of Small Island Developing States (SIDS)
* Maintain balance between large population countries (China/India) which may otherwise get thrown off by the other constraints

## How It Works

### Core Selection Mechanism

The lottery uses a **cumulative population approach** to achieve equal individual probability:

1. **Random Population Position Selection**: The system generates `num_points`random numbers representing positions in a "global population line" (e.g., position 1,234,567 out of ~7.76 billion total population). Please note, population numbers are based on a 2020 dataset.
  
2. **Sequential Population Accumulation**: As the code processes each administrative unit (admin area), it accumulates the population, e.g.:
  
  * If the first admin area has a population of 10,0000 then it corresponds to positions 1 to 10,000
  * If the second admin area has a population of 15,000 then it corresponds to positions 10,001 to 25,000
  * If the third admin area has a population of 3,791 then it corresponds to positions 25,001 to 28,791
  * And so on...
3. **Location Assignment**: When a random population position falls within an admin area's population range, that location is selected. The exact point within the admin area is randomly offset to avoid clustering at centroids.
  
4. **Geographic Randomization**: All admin areas are randomly shuffled before processing to eliminate geographic clustering bias that could occur from the file order.
  

### Why This Ensures Equal Individual Probability

If you pick a random number from 1 to 7.76 billion:

* Densely populated areas (e.g., cities) have more population positions, so they're more likely to be selected
* Sparse areas have fewer positions, so they're less likely to be selected
* **But each individual person has exactly 1/7.76 billion chance** because each position represents one person

**Example:**

* New York: 8 million people (positions 1-8,000,000) → 36.4% chance of selection
* Small town: 10,000 people (positions 50,000,001-50,010,000) → 0.01% chance of selection
* Each individual in both places: exactly 1/7.76 billion chance

### Quota Enforcement System

After initial selection, the system enforces multiple overlapping quota systems through a 5-phase process:

#### Phase 1: Country Quotas

* Each country's maximum representation is calculated as: `ceil(population_percentage × num_points)`
* Countries exceeding their quota have excess people randomly removed
* Removed people are replaced from a backup pool (4×`num_points independently selected locations)

#### Phase 2: Minimum Countries Threshold

* Ensures at least `MIN_COUNTRY_PERCENTAGE`% of all countries are represented (configurable)
* Randomly removes people from countries with >1 person and above half-quota
* Replaces with people from countries with 0 representation
* **Design choice**: Applied early to maximize geographic diversity before other quotas constrain selection

#### Phase 3: UN Region Quotas

* Five UN regional groups: Africa, Asia-Pacific, Eastern Europe, Latin America/Caribbean, Western Europe/Others
* Each region's maximum is based on its total population percentage
* Excess removed randomly, replaced from backup pool

#### Phase 4: Climate Risk Bin Quotas

* Countries are assigned to "climate risk bins" based on climate vulnerability data (bins defined by choices you make in `nd_gain_operations.py`; more than four bins causes large countries to doiminate their bins a bit too much)
* Each bin has a maximum quota (defined in separate configuration files)
* Ensures representation from different climate risk levels
* Countries not in the climate risk dataset go to a "None" bin with no quota limit

#### Phase 5: China-India Balance

* Ensures China and India have balanced representation (difference ≤ 1)
* Applied last because these countries often drive quota violations
* **Design choice**: Separate enforcement because both countries are very large and need special handling

### Special Features

#### Small Island Developing States (SIDS) Guarantee

If enabled (`ENABLE_SIDS_GUARANTEE = True`):

* **Two-phase selection**: SIDS countries below population threshold (2 million) are guaranteed 5% representation
* Phase 1: Select 5-6 points from small SIDS countries first
* Phase 2: Select remaining points from all other countries (with adjusted quotas)
* **Design rationale**:
  * Small island states face disproportionate climate risks but might be underrepresented due to small populations
  * 2 million threshold added to prevent large SIDS countries from being guaranteed a spot when they have a good chance anyway
  * This functionality is based on a pre-prepared list (`SIDS_COUNTRIES_FILE`) which could include other countries based on other/additional criteria if desired

#### Random Shuffling of Data

Before selection, all administrative units are randomly shuffled:

* **Purpose**: Eliminates geographic clustering bias
* **Why needed**: Without shuffling, processing order could create patterns (e.g., all selections from the same continent)
* **Impact**: Ensures true random geographic distribution

#### Backup Pool System

* 4×`num_points` locations are independently selected as backups
* Used during quota enforcement to replace removed people
* Ensures final selection always has exactly `num_points`people
* **Design choice**: Much larger than needed to provide flexibility when quotas are restrictive. The '4' could be changed to any other number as desired.

## Data Sources

* **Population Data**: Gridded Population of the World (GPW) v4 Admin Unit Center Points Population Estimates Rev11
  * [NASA EarthData]([Gridded Population of the World, Version 4 (GPWv4): Administrative Unit Center Points with Population Estimates, Revision 11 | NASA Earthdata](https://www.earthdata.nasa.gov/data/catalog/sedac-ciesin-sedac-gpwv4-aducppe-r11-4.11)) (Please note that over the course of 2025 the location of these files seemed to move a few times, and were even unavailable for a while. This could happen again.)
  * Contains: Administrative unit centroids with 2020 population estimates
* **UN Region Classifications**: Custom file mapping countries to UN regional groups
* **Climate Risk Data**: Processed through `nd_gain_operations.py` to create risk bins !!!!!!!!!!!!!!!!!!!!!!!!!!!

## Output

The system generates:

1. **CSV File**: `outputs/global-assembly-points.csv`
  
  * Latitude/longitude for each selected location
  * Administrative unit name
  * Country information
  * UN region assignment
  * Climate risk bin assignment
  * Summary statistics (country counts, region counts, bin counts)
2. **Visualizations** (interactive Plotly charts):
  
  * World map showing selected locations (before and after quota enforcement)
  * Bar charts comparing quotas vs actual selection (by region, country, climate bin)
  * Maps colored by climate risk bin

## Key Design Choices Explained

### 1. Population-Weighted Random Selection

**Why**: Ensures every person worldwide has equal probability of selection, which is the gold standard for democratic selection processes.

**Alternative considered**: Pure geographic random selection would give equal probability to each location, but this would favor sparsely populated areas and underrepresent cities.

### 2. Post-Selection Quota Enforcement

**Why**: Initial population-weighted selection may violate some of the quotas (e.g. too many people in some countries). Enforcing quotas after selection ensures both fairness (equal individual probability in initial selection) and diversity (quota compliance).

**Alternative considered**: Pre-selection filtering would ensure quotas but would violate the equal individual probability principle.

### 3. Random Shuffling of Data

**Why**: Data files are organized by region/country. Without shuffling, selections could cluster geographically even if random numbers are truly random.

**Impact**: Eliminates any systematic bias from data file organization.

### 4. Multi-Phase Quota Enforcement Order

**Order**: Country → Minimum Countries → Region → Climate Risk → China-India Balance

**Why**:

* Minimum countries early maximizes diversity before other constraints limit options
* China-India balance last because these large countries often drive quota violations
* Climate risk bins can conflict with other quotas, so processed after geographic quotas
* This order was arrived at after considerable experimentation to acheive the optimal compliance with all quotas

### 5. SIDS Two-Phase Selection

**Why**: Small island states are highly vulnerable to climate change but have small populations. Guaranteeing them representation first ensures they're not squeezed out by larger countries.

**Design**: Only applies to SIDS below 2 million population threshold. Larger SIDS (e.g., Dominican Republic, Cuba) compete normally to prevent them from artificially dominating Latin America quotas.

### 6. Backup Pool System

**Why**: Quota enforcement may remove many people. Having a large independent backup pool (4× the needed size) provides flexibility when quotas are restrictive.

**Alternative considered**: Smaller backup pools risk running out of suitable replacements, requiring selection of suboptimal locations.

### 7. Random Offset Within Admin Areas

**Why**: Admin centroids are single points. Adding a random offset within the administrative unit's area distributes selections more evenly across the territory.

**Method**: Calculates admin area as a circle, randomly places point within that radius using spherical geometry. This method is inherited from the original code. It could be improved to consider the shape of the admin area as the circular geometry can result in points landing in other admins areas or in the sea.

## Configuration Options

Key settings at the top of `GCA_2526_Civic_Assembly_location_lottery.py`:

* `num_points = 105`: Number of locations to select
* `total_pop = 7758177449`: Total population from the 2020 GPW v4 r11 dataset; if you use a more up-to-date dataset when available then run the code above where this variable is declared to get the new total
* `climate_risk_caps`: defined by boost method and bin number chosen in `nd_gain_operations.py`
* `ENABLE_SIDS_GUARANTEE = True`: Enable/disable SIDS guarantee
* `SIDS_PERCENTAGE = 0.05`: Percentage of selection from SIDS (5%)
* `SIDS_POPULATION_THRESHOLD = 2000000`: Max population for SIDS guarantee
* `MIN_COUNTRY_PERCENTAGE`: Minimum countries to represent (30% of all countries)
* `RANDOM_SEED = None`: Set to integer for reproducible testing (use `None` for production)
* `SAVE_FIGURES = False`: Save visualization images to disk
* `debug_print = True`: Enable detailed debug output

Also watch out for ISO 3-letter country/region codes being inconsistent and changes in what some regions are called or what countries they are affiliated with.

## File Structure

* `GCA_2526_Civic_Assembly_location_lottery.py`: Main selection script
* `nd_gain_operations.py`: Processes climate risk data to create bins (referenced but not in repo) !!!!!!!!!!!
* `resources/`: Input data files (GPW data, UN region mappings, SIDS lists, climate risk data)
* `outputs/`: Generated CSV files and visualizations

## Running the Code

1. **Install dependencies**:
  
      pip install pandas plotly
  
2. **Download data**:
  
  * GPW v4 Admin Unit Center Points from SEDAC
  * Place in `resources/gpw-v4-admin-unit-center-points-population-estimates-rev11_global_csv/`
3. **Update file paths** in the script:
  
  * `global_pop_admin_centroids_file_root`
  * `other_resources_file_path`
  * `global_pop_output_file_root`
4. **Run**:
  
      python GCA_2526_Civic_Assembly_location_lottery.py
  
5. **Review output**:
  
  * Check `outputs/global-assembly-points.csv` for selected locations
  * Review interactive visualizations
  * Verify quota compliance in summary statistics

## Limitations and Considerations

1. **Admin Unit Granularity**: Selections are at the administrative unit level (not individual addresses). This is a practical limitation of available data.
  
2. **Quota Conflicts**: Some quotas may conflict (e.g., climate risk bin may want more from a country that's at quota). The system handles this through iterative replacement from backups.
  
3. **Missing Data**: Countries not in climate risk dataset are placed in "None" bin with no quota limit.
  
4. **Reproducibility**: Use `RANDOM_SEED` for testing, but set to `None` for production lottery to ensure true randomness.
  
5. **Memory Usage**: Loading all GPW data can use several GB of RAM. The code includes optimizations (essential columns only, data type optimization) to minimize memory usage.
  

## Mathematical Guarantees

* **Equal Individual Probability**: Each person worldwide has probability `num_points / total_pop` of having their location selected in the initial lottery.
* **Quota Compliance**: Final selection respects all configured quota systems (may reduce total below 105 if constraints are too restrictive)
* **Geographic Diversity**: Minimum countries threshold ensures representation from at least 30% of countries
* **Climate Representation**: Climate risk bins ensure proportional representation from different vulnerability levels

## Credits

* **Original code**: April 2020 by Brett Hennig
* **Adapted for GCA Civic Assembly 2025/2026**: Johnny S-D, August 2025
* **Main adaptations**:
  1. Random shuffle of all locations before selection
  2. Climate risk bins as quota caps
  3. SIDS guarantee option
  4. Min countries option
  5. Visualizations for distribution checking
  6. Enhanced debugging and verification

## License

Licensed under GNU General Public License v3.0 as per the original.
