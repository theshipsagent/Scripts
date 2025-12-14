"""
Wetzstein et al. (2020) Spatial Vector Autoregressive Model for Barge Rate Forecasting
Based on: "Transportation Costs: Mississippi River Barge Rates"

This implementation follows the methodology described in the research for forecasting
barge rates using spatial relationships between river segments.
"""

import numpy as np
import pandas as pd
from scipy.spatial.distance import pdist, squareform
from scipy.linalg import inv
from sklearn.metrics import mean_squared_error, mean_absolute_error
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import warnings

warnings.filterwarnings('ignore')


class WetzsteinSpVARModel:
    """
    Spatial Vector Autoregressive Model for Mississippi River Barge Rate Forecasting

    Based on Wetzstein et al. (2020) methodology that incorporates spatial relations
    into a standard vector autoregression model of barge rates.
    """

    def __init__(self, river_segments=None, lags=1, spatial_weight_type='inverse_distance'):
        """
        Initialize the SpVAR model

        Parameters:
        -----------
        river_segments : list
            Names of river segments (default: Wetzstein's 5 segments)
        lags : int
            Number of lags to include in the VAR model
        spatial_weight_type : str
            Type of spatial weight matrix ('inverse_distance', 'contiguity', 'row_standardized')
        """
        if river_segments is None:
            # Wetzstein's 5 river segments
            self.river_segments = [
                'Illinois_River',
                'Upper_Ohio',
                'Lower_Ohio',
                'Lower_Mississippi',
                'St_Louis'
            ]
        else:
            self.river_segments = river_segments

        self.n_segments = len(self.river_segments)
        self.lags = lags
        self.spatial_weight_type = spatial_weight_type

        # Model parameters
        self.spatial_weight_matrix = None
        self.coefficients = None
        self.fitted = False

        # Benchmark tariff rates (1976 cents per ton)
        self.benchmark_rates = {
            'Twin_Cities': 6.19,
            'Mid_Mississippi': 5.32,
            'Illinois_River': 4.64,
            'St_Louis': 3.99,
            'Cincinnati': 4.69,
            'Lower_Ohio': 4.46,
            'Cairo_Memphis': 3.14
        }

    def create_spatial_weight_matrix(self, coordinates=None):
        """
        Create spatial weight matrix W_ij that measures spatial influence
        of river segment i on segment j

        Parameters:
        -----------
        coordinates : array-like, shape (n_segments, 2)
            Coordinates for each river segment (lat, lon)
        """
        if coordinates is None:
            # Approximate coordinates for Wetzstein's segments (lat, lon)
            coordinates = np.array([
                [41.5, -90.5],  # Illinois River
                [39.1, -84.5],  # Upper Ohio
                [37.8, -87.6],  # Lower Ohio
                [29.9, -90.0],  # Lower Mississippi
                [38.6, -90.2]  # St. Louis
            ])

        n = len(coordinates)

        if self.spatial_weight_type == 'inverse_distance':
            # Calculate pairwise distances
            distances = squareform(pdist(coordinates, metric='euclidean'))

            # Create inverse distance matrix
            W = np.zeros((n, n))
            for i in range(n):
                for j in range(n):
                    if i != j and distances[i, j] > 0:
                        W[i, j] = 1.0 / distances[i, j]

        elif self.spatial_weight_type == 'contiguity':
            # Simple contiguity matrix (adjacent segments)
            W = np.zeros((n, n))
            # Define adjacency based on river flow
            adjacency = [(0, 4), (1, 2), (2, 3), (3, 4)]  # Example adjacencies
            for i, j in adjacency:
                W[i, j] = 1.0
                W[j, i] = 1.0

        # Row standardization (as used in Wetzstein et al.)
        row_sums = W.sum(axis=1)
        for i in range(n):
            if row_sums[i] > 0:
                W[i, :] = W[i, :] / row_sums[i]

        self.spatial_weight_matrix = W
        return W

    def prepare_data(self, barge_rates, exogenous_vars=None):
        """
        Prepare data for SpVAR estimation

        Parameters:
        -----------
        barge_rates : DataFrame
            Time series of barge rates for each segment (% of tariff)
        exogenous_vars : DataFrame, optional
            Additional variables (draft depths, diesel prices, etc.)
        """
        # Ensure we have the right segments
        available_segments = [col for col in barge_rates.columns if col in self.river_segments]
        if len(available_segments) != self.n_segments:
            print(f"Warning: Only {len(available_segments)} of {self.n_segments} segments available")
            self.river_segments = available_segments
            self.n_segments = len(available_segments)

        # Create lagged variables
        data = barge_rates[self.river_segments].copy()

        # Add spatial lags (W * y)
        if self.spatial_weight_matrix is not None:
            spatial_lags = pd.DataFrame(
                data.values @ self.spatial_weight_matrix.T,
                index=data.index,
                columns=[f"{seg}_spatial_lag" for seg in self.river_segments]
            )
            data = pd.concat([data, spatial_lags], axis=1)

        # Add temporal lags
        for lag in range(1, self.lags + 1):
            lagged = data.shift(lag)
            lagged.columns = [f"{col}_lag{lag}" for col in lagged.columns]
            data = pd.concat([data, lagged], axis=1)

        # Add exogenous variables if provided
        if exogenous_vars is not None:
            data = pd.concat([data, exogenous_vars], axis=1)

        # Remove NaN rows
        data = data.dropna()

        return data

    def fit(self, barge_rates, exogenous_vars=None, coordinates=None):
        """
        Fit the Spatial Vector Autoregressive model

        Parameters:
        -----------
        barge_rates : DataFrame
            Time series of barge rates (% of tariff)
        exogenous_vars : DataFrame, optional
            Exogenous variables (draft depths, diesel prices, corn storage, etc.)
        coordinates : array-like, optional
            Spatial coordinates for river segments
        """
        print("Fitting Wetzstein SpVAR Model...")

        # Create spatial weight matrix
        if self.spatial_weight_matrix is None:
            self.create_spatial_weight_matrix(coordinates)

        # Prepare data
        data = self.prepare_data(barge_rates, exogenous_vars)

        # Separate dependent and independent variables
        y_cols = [col for col in data.columns if col in self.river_segments]
        X_cols = [col for col in data.columns if col not in self.river_segments]

        Y = data[y_cols].values
        X = data[X_cols].values

        # Add constant term
        X = np.column_stack([np.ones(X.shape[0]), X])

        # Estimate coefficients using OLS for each equation
        self.coefficients = {}
        self.residuals = {}

        for i, segment in enumerate(y_cols):
            # Dependent variable for this segment
            y = Y[:, i]

            # OLS estimation: β = (X'X)^(-1)X'y
            try:
                beta = inv(X.T @ X) @ X.T @ y
                self.coefficients[segment] = beta

                # Calculate residuals
                y_pred = X @ beta
                self.residuals[segment] = y - y_pred

            except np.linalg.LinAlgError:
                print(f"Warning: Singular matrix for {segment}, using pseudo-inverse")
                beta = np.linalg.pinv(X.T @ X) @ X.T @ y
                self.coefficients[segment] = beta
                y_pred = X @ beta
                self.residuals[segment] = y - y_pred

        self.fitted = True
        self.training_data = data
        print("Model fitting completed.")

    def forecast(self, steps_ahead=1, last_data=None):
        """
        Generate forecasts using the fitted SpVAR model

        Parameters:
        -----------
        steps_ahead : int
            Number of periods to forecast ahead
        last_data : DataFrame, optional
            Most recent data for forecasting base
        """
        if not self.fitted:
            raise ValueError("Model must be fitted before forecasting")

        if last_data is None:
            last_data = self.training_data.tail(self.lags)

        forecasts = {}

        for segment in self.river_segments:
            if segment in self.coefficients:
                # Use last available data for forecasting
                X_forecast = self._prepare_forecast_data(last_data, segment)

                # Generate forecast
                beta = self.coefficients[segment]
                forecast_value = X_forecast @ beta
                forecasts[segment] = forecast_value

        return forecasts

    def _prepare_forecast_data(self, last_data, target_segment):
        """
        Prepare data for forecasting a specific segment
        """
        # This is a simplified version - in practice, you'd need to handle
        # the recursive forecasting for multi-step ahead predictions
        feature_cols = [col for col in last_data.columns if col != target_segment]
        X = last_data[feature_cols].iloc[-1].values

        # Add constant term
        X = np.concatenate([[1], X])
        return X

    def calculate_rate_in_dollars(self, percent_tariff, segment):
        """
        Convert percent of tariff to dollars per ton using 1976 benchmarks

        Parameters:
        -----------
        percent_tariff : float
            Rate as percentage of 1976 tariff
        segment : str
            River segment name
        """
        # Map segment names to benchmark rates
        segment_mapping = {
            'Illinois_River': 'Illinois_River',
            'St_Louis': 'St_Louis',
            'Upper_Ohio': 'Lower_Ohio',  # Approximate
            'Lower_Ohio': 'Lower_Ohio',
            'Lower_Mississippi': 'Cairo_Memphis'  # Approximate
        }

        benchmark_key = segment_mapping.get(segment, 'St_Louis')
        benchmark_rate = self.benchmark_rates.get(benchmark_key, 3.99)

        return (percent_tariff * benchmark_rate) / 100

    def evaluate_forecast_accuracy(self, actual_rates, forecasted_rates):
        """
        Evaluate forecast accuracy using various metrics
        """
        metrics = {}

        for segment in self.river_segments:
            if segment in actual_rates and segment in forecasted_rates:
                actual = actual_rates[segment]
                forecast = forecasted_rates[segment]

                if isinstance(actual, (list, np.ndarray)) and isinstance(forecast, (list, np.ndarray)):
                    mse = mean_squared_error(actual, forecast)
                    mae = mean_absolute_error(actual, forecast)
                    mape = np.mean(np.abs((actual - forecast) / actual)) * 100

                    metrics[segment] = {
                        'MSE': mse,
                        'MAE': mae,
                        'MAPE': mape,
                        'RMSE': np.sqrt(mse)
                    }

        return metrics

    def plot_spatial_weights(self):
        """
        Visualize the spatial weight matrix
        """
        if self.spatial_weight_matrix is None:
            print("Spatial weight matrix not created yet")
            return

        plt.figure(figsize=(10, 8))
        sns.heatmap(
            self.spatial_weight_matrix,
            annot=True,
            fmt='.3f',
            xticklabels=self.river_segments,
            yticklabels=self.river_segments,
            cmap='Blues'
        )
        plt.title('Spatial Weight Matrix (W_ij)\nInfluence of Segment i on Segment j')
        plt.tight_layout()
        plt.show()

    def generate_sample_data(self, n_periods=594):
        """
        Generate sample data similar to Wetzstein et al. (2003-2014, 594 observations)
        """
        np.random.seed(42)
        dates = pd.date_range(start='2003-01-01', periods=n_periods, freq='W')

        # Generate synthetic barge rates (% of tariff) with spatial correlation
        base_rates = {
            'Illinois_River': 400,
            'Upper_Ohio': 350,
            'Lower_Ohio': 380,
            'Lower_Mississippi': 320,
            'St_Louis': 360
        }

        data = {}
        for i, segment in enumerate(self.river_segments):
            # Add trend, seasonality, and noise
            trend = np.linspace(0, 50, n_periods)
            seasonal = 30 * np.sin(2 * np.pi * np.arange(n_periods) / 52)  # Annual cycle
            noise = np.random.normal(0, 20, n_periods)

            # Add spatial correlation
            spatial_effect = 0
            if i > 0:
                spatial_effect = 0.3 * data[self.river_segments[i - 1]]

            rates = base_rates[segment] + trend + seasonal + noise + spatial_effect
            data[segment] = np.maximum(rates, 100)  # Minimum 100% of tariff

        barge_rates = pd.DataFrame(data, index=dates)

        # Generate exogenous variables
        exogenous = pd.DataFrame({
            'draft_depth': 9.0 + np.random.normal(0, 0.5, n_periods),
            'diesel_price': 2.5 + 0.5 * np.sin(2 * np.pi * np.arange(n_periods) / 52) + np.random.normal(0, 0.2,
                                                                                                         n_periods),
            'corn_storage': 1000 + 200 * np.sin(2 * np.pi * np.arange(n_periods) / 52) + np.random.normal(0, 50,
                                                                                                          n_periods),
            'grain_movements': 500 + 100 * np.sin(2 * np.pi * np.arange(n_periods) / 52) + np.random.normal(0, 25,
                                                                                                            n_periods)
        }, index=dates)

        return barge_rates, exogenous


def main():
    """
    Example usage of the Wetzstein SpVAR model
    """
    print("Wetzstein Spatial Vector Autoregressive Barge Rate Forecasting Model")
    print("=" * 70)

    # Initialize model
    model = WetzsteinSpVARModel(lags=2, spatial_weight_type='inverse_distance')

    # Generate sample data (similar to Wetzstein's 594 weekly observations)
    print("\n1. Generating sample data (594 weekly observations, 2003-2014)...")
    barge_rates, exogenous_vars = model.generate_sample_data(594)

    print(f"Barge rates shape: {barge_rates.shape}")
    print(f"River segments: {model.river_segments}")
    print(f"\nSample barge rates (% of tariff):")
    print(barge_rates.head())

    # Create and visualize spatial weight matrix
    print("\n2. Creating spatial weight matrix...")
    model.create_spatial_weight_matrix()
    model.plot_spatial_weights()

    # Split data for training and testing (80/20 split as in Wetzstein et al.)
    split_point = int(0.8 * len(barge_rates))
    train_rates = barge_rates.iloc[:split_point]
    test_rates = barge_rates.iloc[split_point:]
    train_exog = exogenous_vars.iloc[:split_point]
    test_exog = exogenous_vars.iloc[split_point:]

    print(f"\n3. Training model on {len(train_rates)} observations...")
    print(f"Testing on {len(test_rates)} observations...")

    # Fit the model
    model.fit(train_rates, train_exog)

    # Generate forecasts
    print("\n4. Generating forecasts...")
    forecasts = model.forecast(steps_ahead=1)

    print("Sample forecasts (% of tariff):")
    for segment, forecast in forecasts.items():
        dollars_per_ton = model.calculate_rate_in_dollars(forecast, segment)
        print(f"{segment}: {forecast:.1f}% of tariff (${dollars_per_ton:.2f}/ton)")

    # Calculate cost savings potential
    print(f"\n5. Potential cost savings analysis:")
    print("Based on Wetzstein et al. findings: 17%-29% savings possible")

    avg_tonnage = 100000  # Example annual tonnage
    avg_rate_improvement = 0.23  # 23% average improvement
    avg_cost_per_ton = 15.00  # Example current cost

    annual_savings = avg_tonnage * avg_cost_per_ton * avg_rate_improvement
    print(f"Example: {avg_tonnage:,} tons/year at ${avg_cost_per_ton}/ton")
    print(f"Potential annual savings: ${annual_savings:,.0f}")

    print(f"\n6. Model Summary:")
    print(f"Segments modeled: {len(model.river_segments)}")
    print(f"Spatial weight matrix: {model.spatial_weight_matrix.shape}")
    print(f"Lags included: {model.lags}")
    print(
        f"Training period: {train_rates.index[0].strftime('%Y-%m-%d')} to {train_rates.index[-1].strftime('%Y-%m-%d')}")


if __name__ == "__main__":
    main()