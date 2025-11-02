# This file contains functions to make ND-GAIN data ready for the geographic lottery
# Written by Johnny S-D August 2025
# Licensed under GNU General Public License v3.0

# It includes a number of ways to boost different bins if you want to over-represent more vulnerable regions

import pandas as pd
import numpy as np
import os
import sys
import matplotlib.pyplot as plt

path_to_reources = "resources/"

gain_data = pd.read_csv(path_to_reources + "gain.csv") # download this as paert oof the ND-GAIN datasety from https://gain.nd.edu/our-work/country-index/

gain_latest_col = gain_data.columns[-1]
gain_latest = gain_data[['ISO3', 'Name', gain_latest_col]]

#chart_title = "no title"

#print(gain_latest)

def clean_gain_data(df, gain_column):
    """
    Clean gain data by removing rows with NaN values in the gain column.
    Returns both cleaned data and filtered out rows.
    
    Args:
        df: DataFrame with ISO3 and gain columns
        gain_column: Name of the gain column to check for NaN values
    
    Returns:
        tuple: (cleaned_df, filtered_df)
    """
    # Create a copy to avoid modifying the original
    df_copy = df.copy()
    
    # Find rows with NaN values in the gain column
    nan_mask = df_copy[gain_column].isna()
    
    # Split into clean and filtered data
    clean_df = df_copy[~nan_mask].reset_index(drop=True)
    filtered_df = df_copy[nan_mask].reset_index(drop=True)

    print(f"Original data length: {len(df_copy)}")
    print(f"Clean data length (after removing NaN): {len(clean_df)}")
    print(f"Filtered out rows: {len(filtered_df)}")

    # Show what was filtered out
    if len(filtered_df) > 0:
        print("\nFiltered out countries (NaN values):")
        print(filtered_df[['ISO3', 'Name']])
    
    return clean_df, filtered_df

def bin_and_normalize(df_to_normalize, bins=10):
    # Filter out NaN values before creating histogram
    clean_data = df_to_normalize.dropna()

    print("Creating histogram from ND-GAIN data")
    
    if len(clean_data) == 0:
        print("Warning: No valid data after removing NaN values")
        return None, None
    
    counts, bins = np.histogram(clean_data, bins=bins)
    #print(f"Counts: {counts}")
    normalized_counts = counts / counts.sum()
    #print(f"Normalized counts: {normalized_counts}")
    #print(f"Checksum: {normalized_counts.sum()}")

    return normalized_counts, bins


# several functions to for adding boosts to the histogram
# these were all originally coded to boost the high end, hence the reversing of the boost array in each

def linear_boost(counts, bins, boost_factor, plot_boost):
    # Apply a linear boost to the histogram. Boost factor is the gradient of a linear function that will be applied to the histogram.
    boost_array = np.array([boost_factor * i for i in range(len(counts))])
    # add 1 to the boost multiplier so that low bins don't disappear
    boost_array = boost_array + 1
    boost_array = boost_array[::-1]
    #normalize the boost array to the max value
    #boost_array = boost_array/max(boost_array)
    print(f"Boost array: {boost_array}")
    if plot_boost:
        plt.plot(np.linspace(bins[0],bins[-1],len(boost_array)),(boost_array/max(boost_array))/10)
        #global chart_title
        #chart_title = f"Linear boost factor: {boost_factor}"
    return counts * boost_array

def polynomial_boost(counts, bins, boost_factor, plot_boost):
    # Apply a polynomial boost to the histogram. Boost factor is the gradient of a polynomial function that will be applied to the histogram.
    boost_array = np.array([i**boost_factor for i in range(len(counts))])
    # add 1 to the boost multiplier so that low bins don't disappear
    #boost_array = boost_array + 1
    boost_array = boost_array[::-1]
    print(f"Boost array: {boost_array}")
    if plot_boost:
        plt.plot(np.linspace(bins[0],bins[-1],len(boost_array)),(boost_array/max(boost_array))/10)
        #global chart_title
        #chart_title = f"Polynomial boost factor: {boost_factor}"
    return counts * boost_array

def exponential_boost(counts, bins, boost_factor, plot_boost):
    # Apply an exponential boost to the histogram. Boost factor is the gradient of an exponential function that will be applied to the histogram.
    boost_array = np.array([np.exp(boost_factor * i) for i in range(len(counts))])
    # add 1 to the boost multiplier so that low bins don't disappear
    #boost_array = boost_array + 1
    boost_array = boost_array[::-1]
    print(f"Boosted array: {boost_array}")
    if plot_boost:
        plt.plot(np.linspace(bins[0],bins[-1],len(boost_array)),(boost_array/max(boost_array))/10)
        #global chart_title
        #chart_title = f"Exponential boost factor: {boost_factor}"
    return counts * boost_array

def flat_then_ramp_at_end_boost(counts, bins, boost_factor, plot_boost):
    # scaling factor of 1 for first 66.7% of bins, then ramping up to boost_factor for last 33.3% of bins
    boost_array = np.array([1 if i < (2/3) * len(counts) else 1 + boost_factor * (i - (2/3) * len(counts)) / ((1/3) * len(counts)) for i in range(len(counts))])
    boost_array = boost_array[::-1]
    print(f"Boosted array: {boost_array}")
    if plot_boost:
        plt.plot(np.linspace(bins[0],bins[-1],len(boost_array)),(boost_array/max(boost_array))/10)
        #global chart_title
        #chart_title = f"Flat (2 3rds) then ramp (1 3rd)boost factor: {boost_factor}"
    return counts * boost_array

def just_boost_the_first_bin(counts, bins, boost_factor=2, plot_boost=False):
    # boost the last bin by boost_factor
    num_bins = len(bins)
    threshold = (((num_bins-1)/num_bins) * len(counts)) - 1
    print('bins: ', bins)
    print('threshold: ', threshold)
    boost_array = np.array([1 if i < threshold else boost_factor for i in range(len(counts))])
    boost_array = boost_array[::-1]
    print(f"Boosted array: {boost_array}")
    if plot_boost:
        plt.plot(np.linspace(bins[0],bins[-1],len(boost_array)),(boost_array/max(boost_array))/10)
        #global chart_title
        #chart_title = f"Just boost the last bin: {boost_factor}"
    return counts * boost_array



def normalize_preserve_relative_min(original_array, scaled_array):
    """
    Alternative approach: preserve the ratio between min and max from original,
    then scale to sum to 1.0
    """
    orig_min = np.min(original_array)
    orig_max = np.max(original_array)
    
    # Get the scaled array range
    scaled_min = np.min(scaled_array)
    scaled_max = np.max(scaled_array)
    
    if scaled_max == scaled_min:
        return np.ones_like(scaled_array) / len(scaled_array)
    
    # Preserve the original min/max ratio
    if orig_max != orig_min:
        target_ratio = orig_min / orig_max
    else:
        target_ratio = 1.0
    
    # Normalize scaled array to [0, 1]
    normalized = (scaled_array - scaled_min) / (scaled_max - scaled_min)
    
    # Apply the ratio: min should be ratio * max
    # If max normalized is 1, then min should be target_ratio
    # Scale so minimum becomes target_ratio and maximum stays 1
    adjusted = normalized * (1 - target_ratio) + target_ratio
    
    # Finally, scale so sum = 1.0
    final_result = adjusted / np.sum(adjusted)
    
    return final_result

def add_a_boost(counts, bins, function_to_apply='none', boost_factor=1, plot_boost=False):
    if function_to_apply == "linear":
        boosted_counts = linear_boost(counts, bins, boost_factor, plot_boost)
    elif function_to_apply == "polynomial":
        boosted_counts = polynomial_boost(counts, bins, boost_factor, plot_boost)
    elif function_to_apply == "exponential":
        boosted_counts = exponential_boost(counts, bins, boost_factor, plot_boost)
    elif function_to_apply == "flat_then_ramp":
        boosted_counts = flat_then_ramp_at_end_boost(counts, bins, boost_factor, plot_boost)
    elif function_to_apply == "just_boost_the_first_bin":
        boosted_counts = just_boost_the_first_bin(counts, bins, boost_factor, plot_boost)
    elif function_to_apply == "none":
        boosted_counts = counts
    else:
        print("Function not found")
        boosted_counts = counts
    print(f"Counts: {counts}")
    print(f"Boosted counts: {boosted_counts}")
    #normalize the boosted counts between pre-boost bin zero value and max post-boost value to prevent bin zero from becoming tiny
    min_val = boosted_counts.min()#counts[0]  # pre-boost value of bin zero
    max_val = boosted_counts.max()  # max post-boost value
    if max_val > min_val:
        normalized_boosted_counts = normalize_preserve_relative_min(counts, boosted_counts) #(boosted_counts - min_val) / (max_val - min_val)
        #normalized_boosted_counts = normalized_boosted_counts + min_val
        #normalized_boosted_counts = normalized_boosted_counts / normalized_boosted_counts.sum()
    else:
        # fallback to standard normalization if all values are the same
        normalized_boosted_counts = boosted_counts / boosted_counts.sum()
    print(f"Normalized boosted counts: {normalized_boosted_counts}")
    print("Checksum after boost: ", normalized_boosted_counts.sum())
    return normalized_boosted_counts
    


def get_gain_bins_and_boosts(function_to_apply='linear', boost_factor=1, bins=10, plot_boost=False):
    """
    Main function to get GAIN data, create bins, and apply boosting.
    
    Args:
        function_to_apply (str): Type of boost function ('linear', 'polynomial', 'exponential', 'flat_then_ramp', 'none')
        boost_factor (float): Factor to control the strength of boosting
        bins (int): Number of histogram bins
    
    Returns:
        tuple: (bin_edges, boosted_counts, original_counts, gain_latest_clean)
            - bin_edges: Array of bin edge values
            - boosted_counts: Array of boosted counts for each bin
            - original_counts: Array of original counts for each bin
            - gain_latest_clean: Cleaned DataFrame with country data
    """
    # Clean the data and keep columns in sync
    gain_latest_clean, gain_latest_filtered = clean_gain_data(gain_data[['ISO3', 'Name', gain_latest_col]], gain_latest_col)
    
    if len(gain_latest_clean) > 0:
        counts, bins_edges = bin_and_normalize(gain_latest_clean[gain_latest_col], bins=bins)
        
        if counts is not None:
            # Apply boosting
            counts_boosted = add_a_boost(counts, bins_edges, function_to_apply=function_to_apply, boost_factor=boost_factor, plot_boost=plot_boost)
            
            return bins_edges, counts_boosted, counts, gain_latest_clean
        else:
            print("No valid data to create bins")
            return None, None, None, None
    else:
        print("No valid data to process")
        return None, None, None, None


def export_a_result(bin_edges, boosted_counts, original_counts, boost_factor, bins, function_to_apply,countries_df=gain_latest):
    # make df for export and add a NaN entry to the end of original and boosted counts to compensate for the bin edge having an extra column
    export_data = pd.DataFrame({'bin_edges': bin_edges, 'original_counts': np.append(original_counts, np.nan), 'boosted_counts': np.append(boosted_counts, np.nan)})
    # add a col for the country lists
    export_data['countries_in_bin_ISO3'] = None
    # add country ISO3s in a list in in the row corresponding to the bin edge
    for i in range(len(bin_edges)-1):
        bin_low = bin_edges[i]
        bin_high = bin_edges[i+1]
        list_for_this_bin=[]
        for row in countries_df.iterrows():
            if row[1][gain_latest_col] >= bin_low and row[1][gain_latest_col] < bin_high:
                list_for_this_bin.append(row[1]['ISO3'])
        export_data.at[i, 'countries_in_bin_ISO3'] = list_for_this_bin

    export_data.to_csv(path_to_reources + f'boosted_data_boost_method_{function_to_apply}_num_bins_{bins}_bins_boosted_by{boost_factor}.csv', index=False)
    print(f"Exported data to boosted_data_boost_method_{function_to_apply}_num_bins_{bins}_bins_boosted_by{boost_factor}.csv")


def main():
    """Main function for testing the GAIN operations"""
    print("Testing GAIN operations...")
    # Test with linear boost
    print("\n=== Testing Linear Boost ===")
    boost_factor = 1
    bin_edges, boosted_counts, original_counts, clean_data = get_gain_bins_and_boosts(
        function_to_apply="linear", 
        boost_factor=boost_factor, 
        bins=10,
        plot_boost=True
    )
    
    if bin_edges is not None:
        print(f"Bin edges: {bin_edges}")
        print(f"Original counts: {original_counts}")
        print(f"Boosted counts: {boosted_counts}")
        
        # Plot the results
        #plt.figure(figsize=(12, 6))
        plt.bar(bin_edges[:-1], original_counts, alpha=0.5, color='blue', label='Original')
        plt.bar(bin_edges[:-1], boosted_counts, alpha=0.5, color='red', label='Boosted')
        plt.legend()
        plt.title(f"Linear Boost: {boost_factor}")
        plt.xlabel('Climate Risk Value')
        plt.ylabel('Count')
        plt.grid(True, alpha=0.3)
        plt.show()
        
        # Test with different boost function
        print("\n=== Testing Exponential Boost ===")
        boost_factor = 0.9
        bin_edges2, boosted_counts2, original_counts2, clean_data2 = get_gain_bins_and_boosts(
            function_to_apply="exponential", 
            boost_factor=boost_factor, 
            bins=10,
            plot_boost=True
        )
        
        if bin_edges2 is not None:
            #plt.figure(figsize=(12, 6))
            plt.bar(bin_edges2[:-1], original_counts2, alpha=0.5, color='blue', label='Original')
            plt.bar(bin_edges2[:-1], boosted_counts2, alpha=0.5, color='red', label='Boosted')
            plt.legend()
            plt.title(f"Exponential Boost: {boost_factor}")
            plt.xlabel('Climate Risk Value')
            plt.ylabel('Count')
            plt.grid(True, alpha=0.3)
            plt.show()

        print("\n=== Testing Polynomial Boost ===")
        boost_factor = 1.3
        bin_edges3, boosted_counts3, original_counts3, clean_data3 = get_gain_bins_and_boosts(
            function_to_apply="polynomial", 
            boost_factor=boost_factor, 
            bins=10,
            plot_boost=True
        )
        
        if bin_edges3 is not None:
            plt.bar(bin_edges3[:-1], original_counts3, alpha=0.5, color='blue', label='Original')
            plt.bar(bin_edges3[:-1], boosted_counts3, alpha=0.5, color='red', label='Boosted')
            plt.legend()
            plt.title(f"Polynomial Boost: {boost_factor}")
            plt.xlabel('Climate Risk Value')
            plt.ylabel('Count')
            plt.grid(True, alpha=0.3)
            plt.show()

        print("\n=== Testing Flat then Ramp Boost ===")
        boost_factor = 4
        bin_edges4, boosted_counts4, original_counts4, clean_data4 = get_gain_bins_and_boosts(
            function_to_apply="flat_then_ramp", 
            boost_factor=boost_factor, 
            bins=10,
            plot_boost=True
        )
        
        if bin_edges4 is not None:
            plt.bar(bin_edges4[:-1], original_counts4, alpha=0.5, color='blue', label='Original')
            plt.bar(bin_edges4[:-1], boosted_counts4, alpha=0.5, color='red', label='Boosted')
            plt.legend()
            plt.title(f"Flat then Ramp Boost: {boost_factor}")
            plt.xlabel('Climate Risk Value')
            plt.ylabel('Count')
            plt.grid(True, alpha=0.3)
            plt.show()

        print("\n=== Testing Just Boost the Last Bin ===")
        boost_factor = 1
        bins=4
        function_to_apply="just_boost_the_first_bin"
        bin_edges5, boosted_counts5, original_counts5, clean_data5 = get_gain_bins_and_boosts(
            function_to_apply=function_to_apply, 
            boost_factor=boost_factor, 
            bins=bins,
            plot_boost=True
        )
        if bin_edges5 is not None:
            plt.bar(bin_edges5[:-1], original_counts5, alpha=0.5, color='blue', label='Original')
            plt.bar(bin_edges5[:-1], boosted_counts5, alpha=0.5, color='red', label='Boosted')
            plt.legend()
            plt.title(f"Just Boost the First Bin: {boost_factor}")
            plt.xlabel('Climate Risk Value')
            plt.ylabel('Count')
            plt.grid(True, alpha=0.3)
            plt.show()

            export_a_result(bin_edges5, boosted_counts5, original_counts5, boost_factor, bins, function_to_apply)



# Run main function if script is run directly
if __name__ == "__main__":
    main()







