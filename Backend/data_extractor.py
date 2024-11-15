import pandas as pd
from langchain.pydantic_v1 import BaseModel, Field
from langchain.tools import BaseTool, StructuredTool, tool
from datetime import datetime
from sklearn.impute import KNNImputer
from sklearn.preprocessing import LabelEncoder
import matplotlib.pyplot as plt
import os
class DataExtractor:
    def __init__(self, csv_file, user_id):
        self.user_id = user_id
        self.data = self.process_data_types(csv_file)
        self.columns = self.get_column_values_info(self.data)
       
        self.data_modifications_tools = [
        # data modification tools
        self.get_tool_data_range(),
        self.tool_get_current_date,
        self.tool_operation_date,
        self.get_tool_filter_numeric(),
        self.get_tool_filter_string(),
        self.get_tool_filter_date(),
        self.get_tool_drop_column()
        ]
        self.process_na_values_tools = [
        # data process na values tools
        self.get_tool_impute_mean_median(),
        self.get_tool_knn_imputation(),
        self.get_tool_impute_mode(),
        self.get_tool_impute_placeholder(),
        self.get_tool_forward_backward_fill(),
        self.get_tool_interpolation(),
        ]
        self.data_analysis_tools = [
        # data anlysis tools
        self.get_tool_descriptive_statistics(),
        self.get_tool_correlation_matrix(),
        self.get_tool_missing_values(),
        self.get_tool_value_counts(),
        self.get_tool_outlier_detection(),
        self.get_tool_trend_analysis(),
        ]
        self.data_graphics_tools = [
        # data graphics tools
        self.get_tool_bar_chart(),
        self.get_tool_histogram(),
        self.get_tool_line_chart(),
        self.get_tool_scatter_plot() 
        ]
        # Combine all tools into a single dictionary
        all_tools = (
            self.data_modifications_tools +
            self.process_na_values_tools +
            self.data_analysis_tools +
            self.data_graphics_tools
        )
        
        # Store the tools in a dictionary by name
        self.tools = {tool.name: tool for tool in all_tools}
 
        
        self.date_columns = [col for col in self.columns if self.columns[col]['dtype'].startswith('datetime')]



    def process_data_types(self, csv_file):
        df = csv_file
        df = self.format_date(df)
        df = df.convert_dtypes()
       

        return df
    def get_column_values_info(self,data):
        print('#############################################')
        print(data.shape)
        dtypes = data.dtypes
        na_sums = data.isna().sum()
        combined_info_dict = {col: {'dtype': str(dtypes[col]), 'na_count': na_sums[col]} for col in data.columns}
   
        return combined_info_dict

    def format_date(self, df):
        string_cols = [col for col, col_type in df.dtypes.items() if col_type == 'object']

        if len(string_cols) > 0:
            mask = df[string_cols].apply(lambda x: x.str.match(r'(\d{2,4}(-|\/|\\|\.| )\d{2}(-|\/|\\|\.| )\d{2,4})+').any(), axis=0)

            df.loc[:, mask.index[mask]] = df.loc[:, mask.index[mask]].apply(pd.to_datetime, dayfirst=False, errors='coerce')

        return df
    
    def create_correlation_matrix(self):
        target_column_name = self.target
        df_corr = self.data.copy()  #Make a copy of the original data
        # Preprocess all the categorical columns
        for col in self.data.select_dtypes(include=['object','string','category']).columns:
            if df_corr[col].nunique() > 10:
                df_corr = pd.get_dummies(df_corr,columns=[col], drop_first=False)
            else:
                label_encoder = LabelEncoder()
                df_corr[col] = label_encoder.fit_transform(df_corr[col])
        # Preprocess all the date time columns
        for col in self.data.select_dtypes(include=['datetime']).columns:
            df_corr[f'{col}_year'] = df_corr[col].dt.year
            df_corr[f'{col}_month'] = df_corr[col].dt.month
            df_corr[f'{col}_day'] = df_corr[col].dt.day
            df_corr[f'{col}_dayofweek'] = df_corr[col].dt.dayofweek

              # Drop the original datetime column
            df_corr.drop(columns=[col], inplace=True)



        print(f"column targer {self.target}")
        corr_matrix = df_corr.corr()[target_column_name]
        corr_matrix.to_csv('correlation_matrix.csv')
    


    ############################# AGENT TOOLS #######################

    # -------- TOOLS FOR DATA MODIFICATION ---------------

    def get_tool_data_range(self):
        @tool
        def tool_data_range(column_name: str, start_date: str, end_date: str) -> str:
            """Extract a date range in the dataframe"""
            start_date = pd.to_datetime(start_date)
            end_date = pd.to_datetime(end_date)
            
            mask = (self.data[column_name] >= start_date) & (self.data[column_name] <= end_date)
            self.data = self.data.loc[mask]
            self.columns = self.get_column_values_info(self.data.loc[mask])
           
            first_date = self.data[column_name].min()
            last_date = self.data[column_name].max()

            return f"The update was succesful, the first date is {first_date} and the last date is {last_date}"

        return tool_data_range
       
    @tool
    def tool_get_current_date() -> str:
        """ Returns the current date in dd-mm-yyyy format."""
        return datetime.now().strftime("%d-%m-%Y")
    
    @tool
    def tool_operation_date(date_str: str, operation: str, years: int) -> str:
        """Adds or subtracts years from a given date.
        Args:
        - date_str: Date in dd-mm-yyyy format (e.g., "09-08-2024").
        - operation: "add" to add years, "subtract" to subtract years.
        - years: Number of years to add or subtract."""
        try:
            date = datetime.strptime(date_str, "%d-%m-%Y")
            if operation == "add":
                new_date = date.replace(year=date.year + years)
            elif operation == "subtract":
                new_date = date.replace(year=date.year - years)
            else:
                raise ValueError("Operation must be 'add' or 'subtract'.")
            
            return new_date.strftime("%d-%m-%Y")
        except Exception as e:
            return f"Error: {e}"
        
    def get_tool_filter_string(self):
        @tool
        def tool_filter_string(column_name: str, string_filter: str, include: bool) -> str:
            """
            Filter rows in a dataframe based on whether a column value starts with or equals a given string.
            If include is True, it includes the rows; otherwise, it excludes them.
            """
            pre_number_rows = len(self.data)
            if include:
                mask = self.data[column_name].str.startswith(string_filter) | (self.data[column_name] == string_filter)
                self.data = self.data[mask]
            else:
                mask = ~(self.data[column_name].str.startswith(string_filter) | (self.data[column_name] == string_filter))
                self.data = self.data[mask]
            
            self.columns = self.get_column_values_info(self.data)
            return f"The data has been filtered succesfully: {pre_number_rows} --> {len(self.data)} rows."
         

        return tool_filter_string
    
    def get_tool_filter_numeric(self):
        @tool
        def tool_filter_numeric(column_name: str, comparison: str, value: float) -> str:
            """
            Filter rows in a dataframe where numeric values in a column meet the specified condition.
            Comparison operators: '>', '<', '=', '>=', '<='
            """
            pre_number_rows = len(self.data)
            if comparison == '>':
                mask = self.data[column_name] > value
            elif comparison == '<':
                mask = self.data[column_name] < value
            elif comparison == '=':
                mask = self.data[column_name] == value
            elif comparison == '>=':
                mask = self.data[column_name] >= value
            elif comparison == '<=':
                mask = self.data[column_name] <= value
            else:
                return "Invalid comparison operator. Use one of: '>', '<', '=', '>=', '<='."
            
            self.data = self.data[mask]
            self.columns = self.get_column_values_info(self.data)
            print("hasta aqui llega")
            return f"The data has been filtered succesfully: {pre_number_rows} --> {len(self.data)} rows."

        return tool_filter_numeric
    
    def get_tool_filter_date(self):
        @tool
        def tool_filter_date(column_name: str, date_part: str, value: int) -> str:
            """
            Filter rows in a dataframe where a date column contains a specific year, month, or day.
            
            Parameters:
            - column_name (str): The name of the column containing date values.
            - date_part (str): The part of the date to filter by ('year', 'month', 'day').
            - value (int): The year, month, or day to filter on.
            """
            pre_number_rows = len(self.data)
            
            # Apply the filter based on the date_part
            if date_part == 'year':
                mask = self.data[column_name].dt.year == value
            elif date_part == 'month':
                mask = self.data[column_name].dt.month == value
            elif date_part == 'day':
                mask = self.data[column_name].dt.day == value
            else:
                return "Invalid date part. Use one of: 'year', 'month', 'day'."
            
            # Filter the data
            self.data = self.data[mask]
            
            
            return f"The data has been filtered by {date_part} successfully: {pre_number_rows} --> {len(self.data)} rows."
    
        return tool_filter_date
    
    
    def get_tool_drop_column(self):
        @tool
        def tool_drop_column(column_name: str) -> str:
            """
            Drop a specified column from the dataframe.
            """
            if column_name in self.data.columns:
                self.data.drop(columns=[column_name], inplace=True)
                self.columns = self.get_column_values_info(self.data)
                return f"Column '{column_name}' was successfully dropped."
            else:
                return f"Column '{column_name}' not found in the dataframe."

        return tool_drop_column


    # -------- TOOLS FOR PROCESSING NA VALUES  ---------------
    def get_tool_missing_values(self):
        @tool
        def tool_missing_values() -> str:
            """
            Analyze and report the percentage of missing values per column.
            """
            total_len = len(self.data)
            missing_values_text = f"Missing values information:\n\n"
            for column_name, value in self.columns.items():
                missing_values_text += f"{column_name}: total:{value['na_count']} --->  {value['na_count']/total_len * 100:.2f}%\n\n"  # Round to 2 decimals
        
            return missing_values_text
            
        return tool_missing_values
    def get_tool_impute_mean_median(self):
        @tool
        def tool_impute_mean_median(column_name: str, strategy: str = "mean") -> str:
            """
        Impute missing values in a numerical column with either the mean or median.
        
        Useful when:
        - Data is numerical (int or float).
        - Missing percentage is low to moderate (e.g., <30%).
        - Mean is used for normally distributed data.
        - Median is used for skewed data.
        """
            if strategy == "mean":
                value_to_fill = self.data[column_name].mean()
            elif strategy == "median":
                value_to_fill = self.data[column_name].median()
            else:
                return "Error: Invalid strategy. Use 'mean' or 'median'."
            
            self.data[column_name].fillna(value_to_fill, inplace=True)
            self.columns = self.get_column_values_info(self.data)
            return f"Imputed missing values in '{column_name}' using {strategy}."
        
        return tool_impute_mean_median
    
    def get_tool_knn_imputation(self):
        @tool
        def tool_knn_imputation(columns: list[str], n_neighbors: int = 5) -> str:
            """
        Perform K-Nearest Neighbors imputation for numerical columns.
        
        Useful when:
        - Data is numerical (int or float).
        - Missing percentage is moderate (e.g., between 10% and 40%).
        - You want to consider the relationships between data points to impute values based on similar rows.
        """
            imputer = KNNImputer(n_neighbors=n_neighbors)
            self.data[columns] = imputer.fit_transform(self.data[columns])
            self.columns = self.get_column_values_info(self.data)
            return f"KNN imputation completed for columns: {', '.join(columns)}."
        
        return tool_knn_imputation
    
    def get_tool_interpolation(self):
        @tool
        def tool_interpolation(column_name: str, method: str = "linear") -> str:
            """
        Perform linear or polynomial interpolation on a time-series column.
        
        Useful when:
        - Data is sequential or time-series (datetime or numerical).
        - Missing percentage is low to moderate (e.g., <20%).
        - You need to estimate missing values between known values in a time series or ordered dataset.
        """
            if method not in ["linear", "polynomial"]:
                return "Error: Invalid interpolation method. Use 'linear' or 'polynomial'."
            
            self.data[column_name].interpolate(method=method, inplace=True)
            self.columns = self.get_column_values_info(self.data)
            return f"Interpolated missing values in '{column_name}' using {method} interpolation."
        
        return tool_interpolation
    
    def get_tool_impute_mode(self):
        @tool
        def tool_impute_mode(column_name: str) -> str:
            """
        Impute missing values in a categorical column using the most frequent value (mode).
        
        Useful when:
        - Data is categorical (strings, categories).
        - Missing percentage is low to moderate (e.g., <20%).
        - There is a dominant category (mode) that represents the majority of the data.
        """
            mode_value = self.data[column_name].mode()[0]
            self.data[column_name].fillna(mode_value, inplace=True)
            self.columns = self.get_column_values_info(self.data)
            return f"Imputed missing values in '{column_name}' using mode (most frequent value)."
        
        return tool_impute_mode
    

    def get_tool_impute_placeholder(self):
        @tool
        def tool_impute_placeholder(column_name: str, placeholder: str = "Unknown") -> str:
            """
        Impute missing values in a categorical column with a placeholder value (e.g., "Unknown").
        
        Useful when:
        - Data is categorical (strings, categories).
        - Missing percentage is moderate to high (e.g., 20% - 50%).
        - The missing data can be safely represented with a placeholder.
        """
            self.data[column_name].fillna(placeholder, inplace=True)
            self.columns = self.get_column_values_info(self.data)
            return f"Imputed missing values in '{column_name}' with placeholder '{placeholder}'."
        
        return tool_impute_placeholder
    

    def get_tool_forward_backward_fill(self):
        @tool
        def tool_forward_backward_fill(column_name: str, direction: str = "forward") -> str:
            """
        Perform forward or backward fill for a datetime column.
        
        Useful when:
        - Data is sequential or time-series (datetime).
        - Missing percentage is low to moderate (e.g., <30%).
        - You want to propagate the most recent (forward fill) or next known value (backward fill).
        """   

            if direction == "forward":
                self.data[column_name].ffill(inplace=True)
            elif direction == "backward":
                self.data[column_name].bfill(inplace=True)
            else:
                return "Error: Invalid direction. Use 'forward' or 'backward'."
                
            self.columns = self.get_column_values_info(self.data)
            return f"Performed {direction} fill on '{column_name}'."
        
            
        
        return tool_forward_backward_fill
# -------- TOOLS FOR CREATE DATA ANALYSYS  ---------------
    def get_tool_descriptive_statistics(self):
        @tool
        def tool_descriptive_statistics(column_name: str) -> str:
            """
            Provide basic descriptive statistics for a given numeric column.
            """
            desc = self.data[column_name].describe()
            stats_text = f"Descriptive stats for {column_name}:\n\n"
            for stat_name, value in desc.items():
                stats_text += f"{stat_name}: {value:.2f}\n\n"  # Round to 2 decimals
        
            return stats_text
        return tool_descriptive_statistics
    
    ## THIS FUCTION HAS TO BE REVIEWED
    def get_tool_correlation_matrix(self):
        @tool
        def tool_correlation_matrix(column_name: str) -> str:
            """
            Calculate and display the correlation matrix for numeric columns, 
            and return the top 5 columns most correlated with the specified column,
            excluding index-related columns.
            """
            # Filter numeric columns only
            numeric_data = self.data.select_dtypes(include=['number'])

            # Exclude likely index columns (e.g., 'id', 'index')
            excluded_columns = [col for col in numeric_data.columns if 'id' in col.lower() or 'index' in col.lower()]
            filtered_data = numeric_data.drop(columns=excluded_columns, errors='ignore')

            # Check if the specified column is in the filtered data
            if column_name not in filtered_data.columns:
                return f"The specified column '{column_name}' is not numeric and cannot be analyzed for correlation."

            # Calculate the correlation matrix
            corr_matrix = filtered_data.corr()

            # Get correlations with the desired column and sort them
            if column_name in corr_matrix.columns:
                sorted_corr = corr_matrix[column_name].abs().sort_values(ascending=False)
                top_5 = sorted_corr.index[1:6]  # Skip the column itself
                top_5_correlations = sorted_corr[1:6] * 100  # Convert to percentage

                # Format the output
                result = f"Top 5 columns most correlated with '{column_name}':\n\n"
                result += "\n\n".join([f"{col}: {corr:.2f}%" for col, corr in zip(top_5, top_5_correlations)])
                return result
            else:
                return f"Column '{column_name}' not found in the numeric columns of the dataset."
            
        return tool_correlation_matrix

    
    
    def get_tool_value_counts(self):
        @tool
        def tool_value_counts(column_name: str) -> str:
            """
            Provide the frequency distribution of a given column.
            """
            value_counts = self.data[column_name].value_counts()
            total_len = len(self.data)
            frequency_text = f"Frequency analysis for {column_name}:\n\n"
            for stat_name, value in value_counts.items():
                frequency_text += f"{stat_name}: total: {value} --> {value/total_len*100:.2f}% \n\n"  # Round to 2 decimals
            return frequency_text
        return tool_value_counts
    
    def get_tool_outlier_detection(self):
        @tool
        def tool_outlier_detection(column_name: str) -> str:
            """
            Detect outliers in a numeric column using the IQR method.
            """
            Q1 = self.data[column_name].quantile(0.25)
            Q3 = self.data[column_name].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            outliers = self.data[(self.data[column_name] < lower_bound) | (self.data[column_name] > upper_bound)][column_name]
            total_len = len(self.data)
            # Create the output message with the percentage of outliers
            outliers_percentage = (len(outliers) / total_len) * 100
            outliers_info = f"Outliers detected: {len(outliers)} rows with outliers in {column_name}, representing {outliers_percentage:.2f}% of the total data.\n\n"
            
            # If there are outliers, add details of up to 5 principal ones
            if not outliers.empty:
                outliers_info += "Principal outliers:\n\n"
                for i in range(min(5, len(outliers))):
                    outlier_value = outliers.iloc[i]
                    outliers_info += f"{i + 1}: {outlier_value}\n\n"
            
            return outliers_info
        return tool_outlier_detection
    
    def get_tool_trend_analysis(self):
        @tool
        def tool_trend_analysis(column_name: str, window: int = 5, seasonality_period: int = None) -> str:
            """
            Perform a trend analysis on a time-series column with a moving average, seasonality check,
            and anomaly detection, providing detailed statistical insights.
            """
            # Calculate moving average
            self.data['moving_average'] = self.data[column_name].rolling(window=window).mean()

            # Trend direction and volatility
            recent_trend = "upward" if self.data['moving_average'].iloc[-1] > self.data['moving_average'].iloc[-window] else "downward"
            overall_trend = "upward" if self.data['moving_average'].iloc[-1] > self.data['moving_average'].iloc[0] else "downward"
            volatility = self.data[column_name].rolling(window=window).std().mean()

            # Stability and changes in direction
            trend_changes = self.data['moving_average'].diff().fillna(0)
            trend_change_count = sum((trend_changes > 0) != (trend_changes.shift(-1) > 0))
            stability = "stable" if trend_change_count < window else "volatile"
            
            # Rate of change and cumulative change
            cumulative_change = ((self.data[column_name].iloc[-1] - self.data[column_name].iloc[0]) / self.data[column_name].iloc[0]) * 100
            avg_rate_of_change = trend_changes.abs().mean()

            # Percentage change in last window and extremes
            recent_percentage_change = ((self.data['moving_average'].iloc[-1] - self.data['moving_average'].iloc[-window]) / self.data['moving_average'].iloc[-window]) * 100
            recent_max = self.data[column_name].iloc[-window:].max()
            recent_min = self.data[column_name].iloc[-window:].min()

            # Seasonality detection (using autocorrelation)
            seasonality_info = ""
            if seasonality_period:
                autocorrelation = self.data[column_name].autocorr(lag=seasonality_period)
                if autocorrelation > 0.7:
                    seasonality_info = f"\nSeasonality detected with a period of {seasonality_period}. Autocorrelation: {autocorrelation:.2f}."
                else:
                    seasonality_info = f"\nNo strong seasonality detected for a period of {seasonality_period}. Autocorrelation: {autocorrelation:.2f}."

            # Return insights
            return (f"Moving average calculated with a window of {window} periods.\n\n"
                    f"Overall trend: {overall_trend}.\n\n"
                    f"Recent trend (last {window} periods): {recent_trend}.\n\n"
                    f"Volatility: {volatility:.2f}.\n\n"
                    f"Trend stability: {stability} with {trend_change_count} directional changes.\n\n"
                    f"Cumulative change: {cumulative_change:.2f}% from start to end.\n\n"
                    f"Average rate of change: {avg_rate_of_change:.2f} units per period.\n\n"
                    f"Recent percentage change in moving average: {recent_percentage_change:.2f}%.\n\n"
                    f"Recent max: {recent_max}, Recent min: {recent_min}.\n\n"
                    f"{seasonality_info}")
        
        return tool_trend_analysis



# -------- TOOLS FOR CREATE GRAPHICS  ---------------

    def get_tool_bar_chart(self):
        @tool
        def tool_bar_chart(column_name: str, color: str = 'red') -> str:
            """
            Create a bar chart showing the frequency of values in a single column.
            """
            # Check if the column is categorical
            if not pd.api.types.is_categorical_dtype(self.data[column_name]) and not pd.api.types.is_object_dtype(self.data[column_name]):
                return f"Error: Column '{column_name}' must be categorical for a bar chart."

            fig, ax = plt.subplots()
            value_counts = self.data[column_name].value_counts()
            value_counts.plot(kind='bar', color=color, ax=ax)
            ax.set_title(f"Bar Chart: {column_name}")
            ax.set_xlabel(column_name)
            ax.set_ylabel("Count")

            # Save the figure
            charts_folder = f'./users_data/{self.user_id}/charts'
            if not os.path.exists(charts_folder):
                os.makedirs(charts_folder)
            
            chart_name = f"bar_chart_{column_name}.png"
            fig_path = os.path.join(charts_folder, chart_name)
            fig.savefig(fig_path)
            
            plt.close(fig)  # Close the figure after saving to free memory
            return f"Figure: {chart_name}"

        return tool_bar_chart




    def get_tool_histogram(self):
        @tool
        def tool_histogram(column_name: str, color: str = 'blue') -> str:
            """
            Create a histogram for a single column.
            For numeric columns, it will create a histogram.
            For categorical columns, it will create a bar chart.
            """
            
            # Check the data type of the column
            if pd.api.types.is_numeric_dtype(self.data[column_name]):
                # For numeric columns, create a histogram
                fig, ax = plt.subplots()
                self.data[column_name].plot(kind='hist', color=color, alpha=0.7, ax=ax)
                ax.set_title(f"Histogram: {column_name}")
                ax.set_xlabel("Value")
                ax.set_ylabel("Frequency")
            else:
                # For categorical columns, create a bar chart
                fig, ax = plt.subplots()
                value_counts = self.data[column_name].value_counts()
                value_counts.plot(kind='bar', color=color, alpha=0.7, ax=ax)
                ax.set_title(f"Bar Chart: {column_name}")
                ax.set_xlabel(column_name)
                ax.set_ylabel("Count")

            # Save the figure to the graphs folder
         
            if not os.path.exists(f'./users_data/{self.user_id}/charts'):
               
                os.makedirs(f'./users_data/{self.user_id}/charts')

            chart_name = f"chart_{column_name}.png"
            fig_path = os.path.join(f'./users_data/{self.user_id}/charts/', chart_name)
           
            fig.savefig(fig_path)

            plt.close(fig)  # Close the figure after saving to free memory

            # Return the name of the chart for later use in the response message
            return f"Figure: {chart_name}"

        return tool_histogram

    
    def get_tool_line_chart(self):
        @tool
        def tool_line_chart(column_name: str, color: str = 'blue') -> str:
            """
            Create a line chart with the index on the x-axis and the values of `column_name` on the y-axis.
            """
            # Check if the column is numeric
            if not pd.api.types.is_numeric_dtype(self.data[column_name]):
                return f"Error: Column '{column_name}' must be numeric for a line chart."

            fig, ax = plt.subplots()
            ax.plot(self.data.index, self.data[column_name], color=color)
            ax.set_title(f"Line Chart: {column_name}")
            ax.set_xlabel("Index")
            ax.set_ylabel(column_name)

            # Save the figure
            charts_folder = f'./users_data/{self.user_id}/charts'
            if not os.path.exists(charts_folder):
                os.makedirs(charts_folder)
            
            chart_name = f"line_chart_{column_name}.png"
            fig_path = os.path.join(charts_folder, chart_name)
            fig.savefig(fig_path)
            
            plt.close(fig)  # Close the figure after saving to free memory
            return f"Figure: {chart_name}"

        return tool_line_chart

    
    def get_tool_scatter_plot(self):
        @tool
        def tool_scatter_plot(x_column: str, y_column: str, color: str = 'red') -> str:
            """
            Create a scatter plot with `x_column` on the x-axis and `y_column` on the y-axis.
            """
            # Check if both columns are numeric
            if x_column not in self.data.columns or y_column not in self.data.columns:
                return f"Error: Columns '{x_column}' and/or '{y_column}' not found in the dataset."
            if not pd.api.types.is_numeric_dtype(self.data[x_column]) or not pd.api.types.is_numeric_dtype(self.data[y_column]):
                return f"Error: Both columns must be numeric for a scatter plot."

            print(f"Creating scatter plot: {x_column} vs {y_column}")
            # Create the scatter plot
            fig, ax = plt.subplots()
            ax.scatter(self.data[x_column], self.data[y_column], color=color)
            ax.set_title(f"Scatter Plot: {x_column} vs {y_column}")
            ax.set_xlabel(x_column)
            ax.set_ylabel(y_column)

            # Save the figure
            charts_folder = f'./users_data/{self.user_id}/charts'
            if not os.path.exists(charts_folder):
                os.makedirs(charts_folder)
            
            chart_name = f"scatter_plot_{x_column}_vs_{y_column}.png"
            fig_path = os.path.join(charts_folder, chart_name)
            fig.savefig(fig_path)

            plt.close(fig)  # Close the figure after saving to free memory
            return f"Figure: {chart_name}"

        return tool_scatter_plot




