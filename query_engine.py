<<<<<<< HEAD
"""
Intelligent Query Engine for Project Samarth - FIXED VERSION
Uses LLM to parse queries and execute data operations
"""

import google.generativeai as genai
import pandas as pd
import json
import re
from typing import Dict, List, Any
import os
from dotenv import load_dotenv

load_dotenv()

class QueryEngine:
    def __init__(self, api_key: str, data: Dict[str, pd.DataFrame]):
        # Validate API key before configuring
        if not api_key or len(api_key) < 30:
            raise ValueError("Invalid API key. Please provide a valid Google Gemini API key.")
        
        try:
            genai.configure(api_key=api_key)
            # Try different model names (API versions vary)
            model_names = ['gemini-pro', 'gemini-1.5-pro', 'gemini-1.0-pro', 'gemini-2.5-flash']
            
            for model_name in model_names:
                try:
                    self.model = genai.GenerativeModel(model_name)
                    test_response = self.model.generate_content("Hi")
                    print(f"✅ API Key validated! Using model: {model_name}")
                    break
                except:
                    continue
            else:
                raise ValueError("No compatible model found")
                
        except Exception as e:
            print(f"❌ API Key validation failed: {e}")
            raise ValueError(f"API key is not valid: {e}")
        
        self.data = data
        try:
            # ✅ Only run cleaning if crop_production dataset exists
            if 'crop_production' in self.data:
                crop_df = self.data['crop_production']

                # ✅ Check if 'District' column actually exists
                if 'District' in crop_df.columns:
                    # Step 1: Clean basic formatting
                    crop_df['District'] = (
                        crop_df['District']
                        .astype(str)
                        .str.strip()
                        .str.replace(r'[^a-zA-Z\s]', '', regex=True)
                        .str.title()
                    )

                    # Step 2: Correct known misspellings / OCR issues
                    corrections = {
                        'Mritsar': 'Amritsar',
                        'Mritsara': 'Amritsar',
                        'Mirtsar': 'Amritsar',
                        'Chnadigarh': 'Chandigarh',
                        'Patila': 'Patiala'
                    }

                    crop_df['District'] = crop_df['District'].replace(corrections)

                    # Step 3: Store the cleaned DataFrame back
                    self.data['crop_production'] = crop_df

        except Exception as e:
            print("⚠️ Warning while cleaning district names:", e)

        # Continue with your schema initialization
        self.data_schema = self._generate_schema()
    
    def _generate_schema(self) -> str:
        """Generate schema description for LLM"""
        schema = []
        
        for name, df in self.data.items():
            schema.append(f"\nDataset: {name}")
            schema.append(f"Columns: {', '.join(df.columns.tolist())}")
            schema.append(f"Sample values:")
            for col in df.columns:
                unique_vals = df[col].unique()[:5]
                schema.append(f"  {col}: {unique_vals}")
        
        return "\n".join(schema)
    
    def parse_query(self, question: str) -> Dict[str, Any]:
        """Use LLM to parse natural language query into structured format"""
        
        prompt = f"""You are a data analysis assistant. Parse the following question into a structured JSON format.

Available datasets and their schemas:
{self.data_schema}

User Question: {question}

Extract the following information and return ONLY a valid JSON object:
{{
    "intent": "compare_rainfall | list_crops | identify_district | analyze_trend | policy_support",
    "states": ["state names mentioned"],
    "districts": ["district names if mentioned"],
    "crops": ["crop names mentioned"],
    "years": ["year range if mentioned"],
    "metrics": ["what to measure: production, rainfall, area, etc"],
    "operations": ["compare", "list", "identify", "correlate", "analyze"],
    "filters": {{"any additional filters"}}
}}

Return ONLY the JSON, no other text."""

        try:
            response = self.model.generate_content(prompt)
            json_str = response.text.strip()
            
            # Extract JSON from markdown if present
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0].strip()
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0].strip()
            
            parsed = json.loads(json_str)
            print(f"✅ Query parsed successfully: {parsed['intent']}")
            return parsed
            
        except Exception as e:
            print(f"⚠️ Error parsing query with LLM: {e}")
            print(f"🔄 Falling back to rule-based parsing...")
            return self._fallback_parse(question)
    
    def _fallback_parse(self, question: str) -> Dict[str, Any]:
        """Fallback rule-based parser when LLM fails"""
        question_lower = question.lower()
        
        # Extract states (Indian states)
        states_keywords = ['punjab', 'haryana', 'up', 'uttar pradesh', 'maharashtra', 
                          'karnataka', 'tamil nadu', 'kerala', 'gujarat', 'rajasthan',
                          'madhya pradesh', 'mp', 'west bengal', 'bihar', 'andhra pradesh']
        states = [s for s in states_keywords if s in question_lower]
        
        # Extract crops
        crop_keywords = ['wheat', 'rice', 'sugarcane', 'cotton', 'maize', 'pulses',
                        'paddy', 'bajra', 'jowar', 'soybean', 'groundnut']
        crops = [c for c in crop_keywords if c in question_lower]
        
        # Extract years (match 4-digit years)
        import re
        years = re.findall(r'\b(19\d{2}|20\d{2})\b', question)
        
        # Extract season
        seasons = []
        if 'rabi' in question_lower:
            seasons.append('Rabi')
        if 'kharif' in question_lower:
            seasons.append('Kharif')
        if 'zaid' in question_lower:
            seasons.append('Zaid')
        
        # Determine intent based on keywords
        if 'district' in question_lower and ('highest' in question_lower or 'maximum' in question_lower or 'most' in question_lower):
            intent = 'identify_district'
        elif 'compare' in question_lower and 'rainfall' in question_lower:
            intent = 'compare_rainfall'
        elif 'trend' in question_lower or 'analyze' in question_lower or 'correlation' in question_lower:
            intent = 'analyze_trend'
        elif 'district' in question_lower:
            intent = 'identify_district'
        else:
            intent = 'compare_rainfall'  # default
        
        # Extract metrics
        metrics = []
        if 'rainfall' in question_lower:
            metrics.append('rainfall')
        if 'production' in question_lower or crops:
            metrics.append('production')
        if 'area' in question_lower:
            metrics.append('area')
        
        parsed = {
            "intent": intent,
            "states": states,
            "crops": crops,
            "years": years,
            "operations": ["compare" if "compare" in question_lower else "identify" if "district" in question_lower else "analyze"],
            "metrics": metrics,
            "filters": {"season": seasons[0] if seasons else None}
        }
        
        print(f"🔄 Fallback parser result: {parsed}")
        return parsed
    
    def execute_query(self, parsed_query: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the parsed query on datasets"""
        
        intent = parsed_query.get("intent", "")
        results = {
            "answer": "",
            "data": {},
            "sources": [],
            "visualizations": []
        }
        
        try:
            # Check for keywords to determine query type
            query_str = str(parsed_query).lower()
            
            # District-level crop queries (highest/lowest production)
            if ("district" in query_str or "highest" in query_str or "lowest" in query_str) and \
               ("crop" in query_str or "production" in query_str or parsed_query.get('crops')):
                results = self._handle_crop_query(parsed_query)
            
            # Rainfall comparison queries
            elif ("rainfall" in query_str and "compare" in query_str) or "compare_rainfall" in intent:
                results = self._handle_rainfall_query(parsed_query)
            
            # Trend analysis queries
            elif "trend" in query_str or "analyze" in query_str or "correlation" in query_str:
                results = self._handle_trend_query(parsed_query)
            
            # Default: try to determine best handler
            else:
                # If has crops and states -> crop query
                if parsed_query.get('crops') and parsed_query.get('states'):
                    results = self._handle_crop_query(parsed_query)
                # If has rainfall metrics -> rainfall query
                elif 'rainfall' in str(parsed_query.get('metrics', [])).lower():
                    results = self._handle_rainfall_query(parsed_query)
                # Otherwise try rainfall as default
                else:
                    results = self._handle_rainfall_query(parsed_query)
                
        except Exception as e:
            print(f"❌ Error executing query: {e}")
            import traceback
            traceback.print_exc()
            results["answer"] = f"Error executing query: {str(e)}"
        
        return results
    
    def _handle_rainfall_query(self, parsed_query: Dict) -> Dict:
        """Handle rainfall comparison queries"""
        df = self.data['rainfall']
        states = parsed_query.get('states', [])
        years = parsed_query.get('years', [])
        
        print(f"🔍 Handling rainfall query for states: {states}, years: {years}")
        
        # Extract "last N years" from query text
        import re
        query_text = str(parsed_query).lower()
        last_n_match = re.search(r'last\s+(\d+)\s+years?', query_text)
        n_years = None
        if last_n_match:
            n_years = int(last_n_match.group(1))
            print(f"📅 Filtering for last {n_years} years")
        
        if len(states) >= 2:
            state1, state2 = states[0].title(), states[1].title()
            
            # Filter data by states
            df1 = df[df['State'].str.contains(state1, case=False, na=False)].copy()
            df2 = df[df['State'].str.contains(state2, case=False, na=False)].copy()
            
            if df1.empty or df2.empty:
                return {
                    "answer": f"❌ No rainfall data found for {state1} or {state2}",
                    "data": {},
                    "sources": []
                }
            
            # Filter by last N years if specified
            if n_years:
                max_year = df['Year'].max()
                min_year = max_year - n_years + 1
                df1 = df1[df1['Year'] >= min_year]
                df2 = df2[df2['Year'] >= min_year]
                year_range = f"{min_year}-{max_year}"
            elif years:
                # Use specific years if provided
                year_list = [int(y) for y in years if str(y).isdigit()]
                if year_list:
                    df1 = df1[df1['Year'].isin(year_list)]
                    df2 = df2[df2['Year'].isin(year_list)]
                    year_range = f"{min(year_list)}-{max(year_list)}"
            else:
                year_range = f"{df1['Year'].min()}-{df1['Year'].max()}"
            
            # Get year-by-year data
            rainfall_by_year_1 = df1.groupby('Year')['Annual_Rainfall_mm'].mean().sort_index()
            rainfall_by_year_2 = df2.groupby('Year')['Annual_Rainfall_mm'].mean().sort_index()
            
            # Calculate averages
            avg1 = rainfall_by_year_1.mean()
            avg2 = rainfall_by_year_2.mean()
            
            # Build detailed year-by-year comparison
            year_comparison = []
            for year in sorted(set(rainfall_by_year_1.index) | set(rainfall_by_year_2.index)):
                rain1 = rainfall_by_year_1.get(year, 0)
                rain2 = rainfall_by_year_2.get(year, 0)
                year_comparison.append(f"  {year}: {state1} = {rain1:.1f} mm, {state2} = {rain2:.1f} mm")
            
            # Get crop data for same states
            crop_df = self.data['crop_production']
            
            # Filter crops by same year range
            crops1 = crop_df[crop_df['State'].str.contains(state1, case=False, na=False)]
            crops2 = crop_df[crop_df['State'].str.contains(state2, case=False, na=False)]
            
            if n_years:
                crops1 = crops1[crops1['Year'] >= min_year]
                crops2 = crops2[crops2['Year'] >= min_year]
            
            top_crops1 = crops1.groupby('Crop')['Production'].sum().nlargest(3)
            top_crops2 = crops2.groupby('Crop')['Production'].sum().nlargest(3)
            
            # Build answer
            answer_parts = [
                f"**Annual Rainfall Comparison: {state1} vs {state2}**",
                f"**Period:** {year_range} ({len(rainfall_by_year_1)} years)\n",
                "**Year-by-Year Rainfall (mm):**"
            ]
            answer_parts.extend(year_comparison)
            
            answer_parts.extend([
                f"\n**Average Annual Rainfall:**",
                f"- {state1}: {avg1:.2f} mm",
                f"- {state2}: {avg2:.2f} mm",
                f"- Difference: {abs(avg1 - avg2):.2f} mm ({state1 if avg1 > avg2 else state2} receives more)\n"
            ])
            
            # Add rainfall trend
            if len(rainfall_by_year_1) > 1:
                trend1 = "increasing" if rainfall_by_year_1.iloc[-1] > rainfall_by_year_1.iloc[0] else "decreasing"
                trend2 = "increasing" if rainfall_by_year_2.iloc[-1] > rainfall_by_year_2.iloc[0] else "decreasing"
                answer_parts.append(f"**Trends:** {state1} is {trend1}, {state2} is {trend2}\n")
            
            answer_parts.extend([
                f"**Top 3 Crops by Production (Same Period):**\n",
                f"**{state1}:**"
            ])
            answer_parts.extend([f"  {i+1}. {crop}: {prod:.0f} tonnes" 
                               for i, (crop, prod) in enumerate(top_crops1.items())])
            
            answer_parts.append(f"\n**{state2}:**")
            answer_parts.extend([f"  {i+1}. {crop}: {prod:.0f} tonnes" 
                               for i, (crop, prod) in enumerate(top_crops2.items())])
            
            answer_parts.append("\n*Data Sources: Ministry of Agriculture & Farmers Welfare, India Meteorological Department (data.gov.in)*")
            
            answer = "\n".join(answer_parts)
            
            return {
                "answer": answer,
                "data": {
                    "rainfall": {state1: avg1, state2: avg2},
                    "rainfall_by_year": {
                        state1: rainfall_by_year_1.to_dict(),
                        state2: rainfall_by_year_2.to_dict()
                    },
                    "crops": {state1: top_crops1.to_dict(), state2: top_crops2.to_dict()},
                    "year_range": year_range
                },
                "sources": ["data.gov.in - IMD Rainfall", "data.gov.in - Agriculture Production"]
            }
        
        return {
            "answer": "⚠️ Please specify at least two states for comparison.", 
            "data": {}, 
            "sources": []
        }
    
    def _handle_crop_query(self, parsed_query: Dict) -> Dict:
        """Handle crop production queries"""
        df = self.data['crop_production']
        states = parsed_query.get('states', [])
        crops = parsed_query.get('crops', [])
        years = parsed_query.get('years', [])
        filters = parsed_query.get('filters', {})
        
        print(f"🔍 Handling crop query - States: {states}, Crops: {crops}")
        
        # Handle single state queries (e.g., "Which district has highest wheat in Punjab?")
        if len(states) >= 1 and crops:
            crop_name = crops[0].title()
            state_name = states[0].title()
            
            # Filter by crop and state
            filtered_df = df[
                (df['Crop'].str.contains(crop_name, case=False, na=False)) &
                (df['State'].str.contains(state_name, case=False, na=False))
            ]
            
            # Apply additional filters (year, season, etc.)
            if years:
                year_val = int(years[0]) if isinstance(years[0], str) and years[0].isdigit() else None
                if year_val:
                    filtered_df = filtered_df[filtered_df['Year'] == year_val]
            
            # Check for season filter in the original query
            season_keywords = {'rabi': 'Rabi', 'kharif': 'Kharif', 'zaid': 'Zaid'}
            if 'Season' in filtered_df.columns:
                for keyword, season in season_keywords.items():
                    if keyword in str(parsed_query).lower():
                        filtered_df = filtered_df[filtered_df['Season'].str.contains(season, case=False, na=False)]
                        break
            
            if filtered_df.empty:
                return {
                    "answer": f"❌ No {crop_name} data found for {state_name}",
                    "data": {},
                    "sources": []
                }
            
            # Find highest production district
            max_row = filtered_df.loc[filtered_df['Production'].idxmax()]
            
            # Build answer with available information
            answer_parts = [f"**{crop_name} Production in {state_name}**\n"]
            answer_parts.append(f"**Highest Production District:**")
            answer_parts.append(f"- District: {max_row['District']}")
            answer_parts.append(f"- Production: {max_row['Production']:.0f} tonnes")
            answer_parts.append(f"- Year: {max_row['Year']}")
            
            if 'Area' in max_row and pd.notna(max_row['Area']):
                answer_parts.append(f"- Area: {max_row['Area']:.0f} hectares")
            if 'Season' in max_row and pd.notna(max_row['Season']):
                answer_parts.append(f"- Season: {max_row['Season']}")
            
            # Add top districts if multiple exist
            top_districts = filtered_df.nlargest(5, 'Production')[['District', 'Production', 'Year']]
            if len(top_districts) > 1:
                answer_parts.append(f"\n**Top 5 Districts by Production:**")
                for idx, row in top_districts.iterrows():
                    answer_parts.append(f"  {row['District']}: {row['Production']:.0f} tonnes ({row['Year']})")
            
            answer_parts.append(f"\n*Source: Ministry of Agriculture & Farmers Welfare via data.gov.in*")
            answer = "\n".join(answer_parts)
            
            return {
                "answer": answer,
                "data": {
                    "highest_district": max_row.to_dict(),
                    "top_districts": top_districts.to_dict('records')
                },
                "sources": ["data.gov.in - Crop Production Statistics"]
            }
        
        # Handle two-state comparison
        elif len(states) >= 2 and crops:
            crop_name = crops[0].title()
            state1, state2 = states[0].title(), states[1].title()
            
            filtered_df = df[df['Crop'].str.contains(crop_name, case=False, na=False)]
            df1 = filtered_df[filtered_df['State'].str.contains(state1, case=False, na=False)]
            df2 = filtered_df[filtered_df['State'].str.contains(state2, case=False, na=False)]
            
            if df1.empty or df2.empty:
                return {
                    "answer": f"❌ No {crop_name} data found for specified states",
                    "data": {},
                    "sources": []
                }
            
            # Get district-level data
            max_district1 = df1.loc[df1['Production'].idxmax()]
            min_district2 = df2.loc[df2['Production'].idxmin()]
            
            answer = f"""
**{crop_name} Production Analysis:**

{state1} - Highest Production:
- District: {max_district1['District']}
- Production: {max_district1['Production']:.0f} tonnes ({max_district1['Year']})

{state2} - Lowest Production:
- District: {min_district2['District']}
- Production: {min_district2['Production']:.0f} tonnes ({min_district2['Year']})

*Source: Ministry of Agriculture & Farmers Welfare via data.gov.in*
"""
            
            return {
                "answer": answer,
                "data": {
                    "max_state1": max_district1.to_dict(),
                    "min_state2": min_district2.to_dict()
                },
                "sources": ["data.gov.in - Crop Production Statistics"]
            }
        
        return {
            "answer": "⚠️ Please specify crop and at least one state.", 
            "data": {}, 
            "sources": []
        }
    
    def _handle_trend_query(self, parsed_query: Dict) -> Dict:
        """Handle trend analysis queries"""
        crop_df = self.data['crop_production']
        rain_df = self.data['rainfall']
        
        crops = parsed_query.get('crops', [])
        states = parsed_query.get('states', [])
        
        if crops and states:
            crop_name = crops[0].title()
            state = states[0].title()
            
            # Filter crop data
            crop_trend = crop_df[
                (crop_df['Crop'].str.contains(crop_name, case=False, na=False)) &
                (crop_df['State'].str.contains(state, case=False, na=False))
            ].groupby('Year')['Production'].sum()
            
            # Filter rainfall data
            rain_trend = rain_df[
                rain_df['State'].str.contains(state, case=False, na=False)
            ].groupby('Year')['Annual_Rainfall_mm'].mean()
            
            if crop_trend.empty or rain_trend.empty:
                return {
                    "answer": f"❌ No trend data found for {crop_name} in {state}",
                    "data": {},
                    "sources": []
                }
            
            # Calculate correlation
            merged = pd.DataFrame({
                'production': crop_trend,
                'rainfall': rain_trend
            }).dropna()
            
            if len(merged) > 1:
                correlation = merged['production'].corr(merged['rainfall'])
                
                answer = f"""
**Trend Analysis: {crop_name} in {state}**

Production Trend (Last {len(crop_trend)} years):
{chr(10).join([f'  {year}: {prod:.0f} tonnes' for year, prod in crop_trend.items()])}

Rainfall Trend (Same Period):
{chr(10).join([f'  {year}: {rain:.0f} mm' for year, rain in rain_trend.items()])}

**Correlation Analysis:**
Correlation coefficient: {correlation:.3f}
{self._interpret_correlation(correlation)}

*Sources: Agriculture Production Data & IMD Rainfall Data (data.gov.in)*
"""
                
                return {
                    "answer": answer,
                    "data": {
                        "crop_trend": crop_trend.to_dict(),
                        "rainfall_trend": rain_trend.to_dict(),
                        "correlation": correlation
                    },
                    "sources": ["data.gov.in - Agriculture & IMD"]
                }
        
        return {
            "answer": "⚠️ Please specify crop and region.", 
            "data": {}, 
            "sources": []
        }
    
    def _handle_general_query(self, parsed_query: Dict) -> Dict:
        """Handle general queries using LLM"""
        
        # Prepare data summary
        summary = "Available data summary:\n"
        for name, df in self.data.items():
            summary += f"\n{name}:\n{df.describe()}\n"
        
        prompt = f"""Based on this data, answer the question:

{summary}

Question: {parsed_query}

Provide a data-driven answer with specific numbers and cite sources."""

        try:
            response = self.model.generate_content(prompt)
            return {
                "answer": response.text,
                "data": {},
                "sources": ["data.gov.in datasets"]
            }
        except Exception as e:
            return {
                "answer": f"❌ Error: {e}", 
                "data": {}, 
                "sources": []
            }
    
    def _interpret_correlation(self, corr: float) -> str:
        """Interpret correlation coefficient"""
        if corr > 0.7:
            return "✅ Strong positive correlation: Higher rainfall associated with higher production."
        elif corr > 0.3:
            return "📈 Moderate positive correlation: Rainfall shows some positive influence."
        elif corr > -0.3:
            return "➡️ Weak correlation: Little relationship between rainfall and production."
        elif corr > -0.7:
            return "📉 Moderate negative correlation: Higher rainfall associated with lower production."
        else:
            return "⚠️ Strong negative correlation: Significant inverse relationship."
    
    def answer_question(self, question: str) -> Dict[str, Any]:
        """Main entry point: parse and execute query"""
        print(f"\n{'='*60}")
        print(f"🔍 Processing: {question}")
        print(f"{'='*60}")
        
        # Parse query
        parsed = self.parse_query(question)
        print(f"📋 Parsed intent: {parsed.get('intent', 'unknown')}")
        print(f"📍 States: {parsed.get('states', [])}")
        print(f"🌾 Crops: {parsed.get('crops', [])}")
        
        # Execute query
        result = self.execute_query(parsed)
        
        print(f"\n✅ Query completed!")
        print(f"{'='*60}\n")
        
        return result


if __name__ == "__main__":
    print("🌾 Project Samarth - Query Engine Test\n")
    
    # Check for API key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not found in environment")
        print("\n📝 To fix this:")
        print("1. Get API key from: https://aistudio.google.com/app/apikey")
        print("2. Create .env file with: GEMINI_API_KEY=your_key_here")
        print("3. Or set environment variable: export GEMINI_API_KEY='your_key'")
        exit(1)
    
    print(f"🔑 API Key found: {api_key[:20]}...")
    
    # Example dummy data
    rainfall_df = pd.DataFrame({
        'State': ['Punjab', 'Haryana', 'Punjab', 'Haryana'] * 3,
        'Year': [2020, 2020, 2021, 2021, 2022, 2022, 2023, 2023, 2024, 2024, 2025, 2025],
        'Annual_Rainfall_mm': [780, 620, 800, 640, 790, 630, 810, 650, 795, 635, 805, 645]
    })

    crop_df = pd.DataFrame({
        'State': ['Punjab', 'Haryana', 'Punjab', 'Haryana'] * 3,
        'District': ['Amritsar', 'Hisar', 'Ludhiana', 'Rohtak'] * 3,
        'Crop': ['Wheat', 'Wheat', 'Rice', 'Rice'] * 3,
        'Year': [2020, 2020, 2021, 2021, 2022, 2022, 2023, 2023, 2024, 2024, 2025, 2025],
        'Production': [1200, 1000, 1400, 900, 1250, 1050, 1450, 950, 1300, 1100, 1500, 1000]
    })

    data = {
        'rainfall': rainfall_df,
        'crop_production': crop_df
    }

    try:
        engine = QueryEngine(api_key=api_key, data=data)
        
        # Run test query
        question = "Compare rainfall and crop production between Punjab and Haryana."
        result = engine.answer_question(question)
        
        print("\n📊 RESULT:")
        print(result["answer"])
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
=======
"""
Intelligent Query Engine for Project Samarth - FIXED VERSION
Uses LLM to parse queries and execute data operations
"""

import google.generativeai as genai
import pandas as pd
import json
import re
from typing import Dict, List, Any
import os
from dotenv import load_dotenv

load_dotenv()

class QueryEngine:
    def __init__(self, api_key: str, data: Dict[str, pd.DataFrame]):
        # Validate API key before configuring
        if not api_key or len(api_key) < 30:
            raise ValueError("Invalid API key. Please provide a valid Google Gemini API key.")
        
        try:
            genai.configure(api_key=api_key)
            # Try different model names (API versions vary)
            model_names = ['gemini-pro', 'gemini-1.5-pro', 'gemini-1.0-pro', 'gemini-2.5-flash']
            
            for model_name in model_names:
                try:
                    self.model = genai.GenerativeModel(model_name)
                    test_response = self.model.generate_content("Hi")
                    print(f"✅ API Key validated! Using model: {model_name}")
                    break
                except:
                    continue
            else:
                raise ValueError("No compatible model found")
                
        except Exception as e:
            print(f"❌ API Key validation failed: {e}")
            raise ValueError(f"API key is not valid: {e}")
        
        self.data = data
        try:
            # ✅ Only run cleaning if crop_production dataset exists
            if 'crop_production' in self.data:
                crop_df = self.data['crop_production']

                # ✅ Check if 'District' column actually exists
                if 'District' in crop_df.columns:
                    # Step 1: Clean basic formatting
                    crop_df['District'] = (
                        crop_df['District']
                        .astype(str)
                        .str.strip()
                        .str.replace(r'[^a-zA-Z\s]', '', regex=True)
                        .str.title()
                    )

                    # Step 2: Correct known misspellings / OCR issues
                    corrections = {
                        'Mritsar': 'Amritsar',
                        'Mritsara': 'Amritsar',
                        'Mirtsar': 'Amritsar',
                        'Chnadigarh': 'Chandigarh',
                        'Patila': 'Patiala'
                    }

                    crop_df['District'] = crop_df['District'].replace(corrections)

                    # Step 3: Store the cleaned DataFrame back
                    self.data['crop_production'] = crop_df

        except Exception as e:
            print("⚠️ Warning while cleaning district names:", e)

        # Continue with your schema initialization
        self.data_schema = self._generate_schema()
    
    def _generate_schema(self) -> str:
        """Generate schema description for LLM"""
        schema = []
        
        for name, df in self.data.items():
            schema.append(f"\nDataset: {name}")
            schema.append(f"Columns: {', '.join(df.columns.tolist())}")
            schema.append(f"Sample values:")
            for col in df.columns:
                unique_vals = df[col].unique()[:5]
                schema.append(f"  {col}: {unique_vals}")
        
        return "\n".join(schema)
    
    def parse_query(self, question: str) -> Dict[str, Any]:
        """Use LLM to parse natural language query into structured format"""
        
        prompt = f"""You are a data analysis assistant. Parse the following question into a structured JSON format.

Available datasets and their schemas:
{self.data_schema}

User Question: {question}

Extract the following information and return ONLY a valid JSON object:
{{
    "intent": "compare_rainfall | list_crops | identify_district | analyze_trend | policy_support",
    "states": ["state names mentioned"],
    "districts": ["district names if mentioned"],
    "crops": ["crop names mentioned"],
    "years": ["year range if mentioned"],
    "metrics": ["what to measure: production, rainfall, area, etc"],
    "operations": ["compare", "list", "identify", "correlate", "analyze"],
    "filters": {{"any additional filters"}}
}}

Return ONLY the JSON, no other text."""

        try:
            response = self.model.generate_content(prompt)
            json_str = response.text.strip()
            
            # Extract JSON from markdown if present
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0].strip()
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0].strip()
            
            parsed = json.loads(json_str)
            print(f"✅ Query parsed successfully: {parsed['intent']}")
            return parsed
            
        except Exception as e:
            print(f"⚠️ Error parsing query with LLM: {e}")
            print(f"🔄 Falling back to rule-based parsing...")
            return self._fallback_parse(question)
    
    def _fallback_parse(self, question: str) -> Dict[str, Any]:
        """Fallback rule-based parser when LLM fails"""
        question_lower = question.lower()
        
        # Extract states (Indian states)
        states_keywords = ['punjab', 'haryana', 'up', 'uttar pradesh', 'maharashtra', 
                          'karnataka', 'tamil nadu', 'kerala', 'gujarat', 'rajasthan',
                          'madhya pradesh', 'mp', 'west bengal', 'bihar', 'andhra pradesh']
        states = [s for s in states_keywords if s in question_lower]
        
        # Extract crops
        crop_keywords = ['wheat', 'rice', 'sugarcane', 'cotton', 'maize', 'pulses',
                        'paddy', 'bajra', 'jowar', 'soybean', 'groundnut']
        crops = [c for c in crop_keywords if c in question_lower]
        
        # Extract years (match 4-digit years)
        import re
        years = re.findall(r'\b(19\d{2}|20\d{2})\b', question)
        
        # Extract season
        seasons = []
        if 'rabi' in question_lower:
            seasons.append('Rabi')
        if 'kharif' in question_lower:
            seasons.append('Kharif')
        if 'zaid' in question_lower:
            seasons.append('Zaid')
        
        # Determine intent based on keywords
        if 'district' in question_lower and ('highest' in question_lower or 'maximum' in question_lower or 'most' in question_lower):
            intent = 'identify_district'
        elif 'compare' in question_lower and 'rainfall' in question_lower:
            intent = 'compare_rainfall'
        elif 'trend' in question_lower or 'analyze' in question_lower or 'correlation' in question_lower:
            intent = 'analyze_trend'
        elif 'district' in question_lower:
            intent = 'identify_district'
        else:
            intent = 'compare_rainfall'  # default
        
        # Extract metrics
        metrics = []
        if 'rainfall' in question_lower:
            metrics.append('rainfall')
        if 'production' in question_lower or crops:
            metrics.append('production')
        if 'area' in question_lower:
            metrics.append('area')
        
        parsed = {
            "intent": intent,
            "states": states,
            "crops": crops,
            "years": years,
            "operations": ["compare" if "compare" in question_lower else "identify" if "district" in question_lower else "analyze"],
            "metrics": metrics,
            "filters": {"season": seasons[0] if seasons else None}
        }
        
        print(f"🔄 Fallback parser result: {parsed}")
        return parsed
    
    def execute_query(self, parsed_query: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the parsed query on datasets"""
        
        intent = parsed_query.get("intent", "")
        results = {
            "answer": "",
            "data": {},
            "sources": [],
            "visualizations": []
        }
        
        try:
            # Check for keywords to determine query type
            query_str = str(parsed_query).lower()
            
            # District-level crop queries (highest/lowest production)
            if ("district" in query_str or "highest" in query_str or "lowest" in query_str) and \
               ("crop" in query_str or "production" in query_str or parsed_query.get('crops')):
                results = self._handle_crop_query(parsed_query)
            
            # Rainfall comparison queries
            elif ("rainfall" in query_str and "compare" in query_str) or "compare_rainfall" in intent:
                results = self._handle_rainfall_query(parsed_query)
            
            # Trend analysis queries
            elif "trend" in query_str or "analyze" in query_str or "correlation" in query_str:
                results = self._handle_trend_query(parsed_query)
            
            # Default: try to determine best handler
            else:
                # If has crops and states -> crop query
                if parsed_query.get('crops') and parsed_query.get('states'):
                    results = self._handle_crop_query(parsed_query)
                # If has rainfall metrics -> rainfall query
                elif 'rainfall' in str(parsed_query.get('metrics', [])).lower():
                    results = self._handle_rainfall_query(parsed_query)
                # Otherwise try rainfall as default
                else:
                    results = self._handle_rainfall_query(parsed_query)
                
        except Exception as e:
            print(f"❌ Error executing query: {e}")
            import traceback
            traceback.print_exc()
            results["answer"] = f"Error executing query: {str(e)}"
        
        return results
    
    def _handle_rainfall_query(self, parsed_query: Dict) -> Dict:
        """Handle rainfall comparison queries"""
        df = self.data['rainfall']
        states = parsed_query.get('states', [])
        years = parsed_query.get('years', [])
        
        print(f"🔍 Handling rainfall query for states: {states}, years: {years}")
        
        # Extract "last N years" from query text
        import re
        query_text = str(parsed_query).lower()
        last_n_match = re.search(r'last\s+(\d+)\s+years?', query_text)
        n_years = None
        if last_n_match:
            n_years = int(last_n_match.group(1))
            print(f"📅 Filtering for last {n_years} years")
        
        if len(states) >= 2:
            state1, state2 = states[0].title(), states[1].title()
            
            # Filter data by states
            df1 = df[df['State'].str.contains(state1, case=False, na=False)].copy()
            df2 = df[df['State'].str.contains(state2, case=False, na=False)].copy()
            
            if df1.empty or df2.empty:
                return {
                    "answer": f"❌ No rainfall data found for {state1} or {state2}",
                    "data": {},
                    "sources": []
                }
            
            # Filter by last N years if specified
            if n_years:
                max_year = df['Year'].max()
                min_year = max_year - n_years + 1
                df1 = df1[df1['Year'] >= min_year]
                df2 = df2[df2['Year'] >= min_year]
                year_range = f"{min_year}-{max_year}"
            elif years:
                # Use specific years if provided
                year_list = [int(y) for y in years if str(y).isdigit()]
                if year_list:
                    df1 = df1[df1['Year'].isin(year_list)]
                    df2 = df2[df2['Year'].isin(year_list)]
                    year_range = f"{min(year_list)}-{max(year_list)}"
            else:
                year_range = f"{df1['Year'].min()}-{df1['Year'].max()}"
            
            # Get year-by-year data
            rainfall_by_year_1 = df1.groupby('Year')['Annual_Rainfall_mm'].mean().sort_index()
            rainfall_by_year_2 = df2.groupby('Year')['Annual_Rainfall_mm'].mean().sort_index()
            
            # Calculate averages
            avg1 = rainfall_by_year_1.mean()
            avg2 = rainfall_by_year_2.mean()
            
            # Build detailed year-by-year comparison
            year_comparison = []
            for year in sorted(set(rainfall_by_year_1.index) | set(rainfall_by_year_2.index)):
                rain1 = rainfall_by_year_1.get(year, 0)
                rain2 = rainfall_by_year_2.get(year, 0)
                year_comparison.append(f"  {year}: {state1} = {rain1:.1f} mm, {state2} = {rain2:.1f} mm")
            
            # Get crop data for same states
            crop_df = self.data['crop_production']
            
            # Filter crops by same year range
            crops1 = crop_df[crop_df['State'].str.contains(state1, case=False, na=False)]
            crops2 = crop_df[crop_df['State'].str.contains(state2, case=False, na=False)]
            
            if n_years:
                crops1 = crops1[crops1['Year'] >= min_year]
                crops2 = crops2[crops2['Year'] >= min_year]
            
            top_crops1 = crops1.groupby('Crop')['Production'].sum().nlargest(3)
            top_crops2 = crops2.groupby('Crop')['Production'].sum().nlargest(3)
            
            # Build answer
            answer_parts = [
                f"**Annual Rainfall Comparison: {state1} vs {state2}**",
                f"**Period:** {year_range} ({len(rainfall_by_year_1)} years)\n",
                "**Year-by-Year Rainfall (mm):**"
            ]
            answer_parts.extend(year_comparison)
            
            answer_parts.extend([
                f"\n**Average Annual Rainfall:**",
                f"- {state1}: {avg1:.2f} mm",
                f"- {state2}: {avg2:.2f} mm",
                f"- Difference: {abs(avg1 - avg2):.2f} mm ({state1 if avg1 > avg2 else state2} receives more)\n"
            ])
            
            # Add rainfall trend
            if len(rainfall_by_year_1) > 1:
                trend1 = "increasing" if rainfall_by_year_1.iloc[-1] > rainfall_by_year_1.iloc[0] else "decreasing"
                trend2 = "increasing" if rainfall_by_year_2.iloc[-1] > rainfall_by_year_2.iloc[0] else "decreasing"
                answer_parts.append(f"**Trends:** {state1} is {trend1}, {state2} is {trend2}\n")
            
            answer_parts.extend([
                f"**Top 3 Crops by Production (Same Period):**\n",
                f"**{state1}:**"
            ])
            answer_parts.extend([f"  {i+1}. {crop}: {prod:.0f} tonnes" 
                               for i, (crop, prod) in enumerate(top_crops1.items())])
            
            answer_parts.append(f"\n**{state2}:**")
            answer_parts.extend([f"  {i+1}. {crop}: {prod:.0f} tonnes" 
                               for i, (crop, prod) in enumerate(top_crops2.items())])
            
            answer_parts.append("\n*Data Sources: Ministry of Agriculture & Farmers Welfare, India Meteorological Department (data.gov.in)*")
            
            answer = "\n".join(answer_parts)
            
            return {
                "answer": answer,
                "data": {
                    "rainfall": {state1: avg1, state2: avg2},
                    "rainfall_by_year": {
                        state1: rainfall_by_year_1.to_dict(),
                        state2: rainfall_by_year_2.to_dict()
                    },
                    "crops": {state1: top_crops1.to_dict(), state2: top_crops2.to_dict()},
                    "year_range": year_range
                },
                "sources": ["data.gov.in - IMD Rainfall", "data.gov.in - Agriculture Production"]
            }
        
        return {
            "answer": "⚠️ Please specify at least two states for comparison.", 
            "data": {}, 
            "sources": []
        }
    
    def _handle_crop_query(self, parsed_query: Dict) -> Dict:
        """Handle crop production queries"""
        df = self.data['crop_production']
        states = parsed_query.get('states', [])
        crops = parsed_query.get('crops', [])
        years = parsed_query.get('years', [])
        filters = parsed_query.get('filters', {})
        
        print(f"🔍 Handling crop query - States: {states}, Crops: {crops}")
        
        # Handle single state queries (e.g., "Which district has highest wheat in Punjab?")
        if len(states) >= 1 and crops:
            crop_name = crops[0].title()
            state_name = states[0].title()
            
            # Filter by crop and state
            filtered_df = df[
                (df['Crop'].str.contains(crop_name, case=False, na=False)) &
                (df['State'].str.contains(state_name, case=False, na=False))
            ]
            
            # Apply additional filters (year, season, etc.)
            if years:
                year_val = int(years[0]) if isinstance(years[0], str) and years[0].isdigit() else None
                if year_val:
                    filtered_df = filtered_df[filtered_df['Year'] == year_val]
            
            # Check for season filter in the original query
            season_keywords = {'rabi': 'Rabi', 'kharif': 'Kharif', 'zaid': 'Zaid'}
            if 'Season' in filtered_df.columns:
                for keyword, season in season_keywords.items():
                    if keyword in str(parsed_query).lower():
                        filtered_df = filtered_df[filtered_df['Season'].str.contains(season, case=False, na=False)]
                        break
            
            if filtered_df.empty:
                return {
                    "answer": f"❌ No {crop_name} data found for {state_name}",
                    "data": {},
                    "sources": []
                }
            
            # Find highest production district
            max_row = filtered_df.loc[filtered_df['Production'].idxmax()]
            
            # Build answer with available information
            answer_parts = [f"**{crop_name} Production in {state_name}**\n"]
            answer_parts.append(f"**Highest Production District:**")
            answer_parts.append(f"- District: {max_row['District']}")
            answer_parts.append(f"- Production: {max_row['Production']:.0f} tonnes")
            answer_parts.append(f"- Year: {max_row['Year']}")
            
            if 'Area' in max_row and pd.notna(max_row['Area']):
                answer_parts.append(f"- Area: {max_row['Area']:.0f} hectares")
            if 'Season' in max_row and pd.notna(max_row['Season']):
                answer_parts.append(f"- Season: {max_row['Season']}")
            
            # Add top districts if multiple exist
            top_districts = filtered_df.nlargest(5, 'Production')[['District', 'Production', 'Year']]
            if len(top_districts) > 1:
                answer_parts.append(f"\n**Top 5 Districts by Production:**")
                for idx, row in top_districts.iterrows():
                    answer_parts.append(f"  {row['District']}: {row['Production']:.0f} tonnes ({row['Year']})")
            
            answer_parts.append(f"\n*Source: Ministry of Agriculture & Farmers Welfare via data.gov.in*")
            answer = "\n".join(answer_parts)
            
            return {
                "answer": answer,
                "data": {
                    "highest_district": max_row.to_dict(),
                    "top_districts": top_districts.to_dict('records')
                },
                "sources": ["data.gov.in - Crop Production Statistics"]
            }
        
        # Handle two-state comparison
        elif len(states) >= 2 and crops:
            crop_name = crops[0].title()
            state1, state2 = states[0].title(), states[1].title()
            
            filtered_df = df[df['Crop'].str.contains(crop_name, case=False, na=False)]
            df1 = filtered_df[filtered_df['State'].str.contains(state1, case=False, na=False)]
            df2 = filtered_df[filtered_df['State'].str.contains(state2, case=False, na=False)]
            
            if df1.empty or df2.empty:
                return {
                    "answer": f"❌ No {crop_name} data found for specified states",
                    "data": {},
                    "sources": []
                }
            
            # Get district-level data
            max_district1 = df1.loc[df1['Production'].idxmax()]
            min_district2 = df2.loc[df2['Production'].idxmin()]
            
            answer = f"""
**{crop_name} Production Analysis:**

{state1} - Highest Production:
- District: {max_district1['District']}
- Production: {max_district1['Production']:.0f} tonnes ({max_district1['Year']})

{state2} - Lowest Production:
- District: {min_district2['District']}
- Production: {min_district2['Production']:.0f} tonnes ({min_district2['Year']})

*Source: Ministry of Agriculture & Farmers Welfare via data.gov.in*
"""
            
            return {
                "answer": answer,
                "data": {
                    "max_state1": max_district1.to_dict(),
                    "min_state2": min_district2.to_dict()
                },
                "sources": ["data.gov.in - Crop Production Statistics"]
            }
        
        return {
            "answer": "⚠️ Please specify crop and at least one state.", 
            "data": {}, 
            "sources": []
        }
    
    def _handle_trend_query(self, parsed_query: Dict) -> Dict:
        """Handle trend analysis queries"""
        crop_df = self.data['crop_production']
        rain_df = self.data['rainfall']
        
        crops = parsed_query.get('crops', [])
        states = parsed_query.get('states', [])
        
        if crops and states:
            crop_name = crops[0].title()
            state = states[0].title()
            
            # Filter crop data
            crop_trend = crop_df[
                (crop_df['Crop'].str.contains(crop_name, case=False, na=False)) &
                (crop_df['State'].str.contains(state, case=False, na=False))
            ].groupby('Year')['Production'].sum()
            
            # Filter rainfall data
            rain_trend = rain_df[
                rain_df['State'].str.contains(state, case=False, na=False)
            ].groupby('Year')['Annual_Rainfall_mm'].mean()
            
            if crop_trend.empty or rain_trend.empty:
                return {
                    "answer": f"❌ No trend data found for {crop_name} in {state}",
                    "data": {},
                    "sources": []
                }
            
            # Calculate correlation
            merged = pd.DataFrame({
                'production': crop_trend,
                'rainfall': rain_trend
            }).dropna()
            
            if len(merged) > 1:
                correlation = merged['production'].corr(merged['rainfall'])
                
                answer = f"""
**Trend Analysis: {crop_name} in {state}**

Production Trend (Last {len(crop_trend)} years):
{chr(10).join([f'  {year}: {prod:.0f} tonnes' for year, prod in crop_trend.items()])}

Rainfall Trend (Same Period):
{chr(10).join([f'  {year}: {rain:.0f} mm' for year, rain in rain_trend.items()])}

**Correlation Analysis:**
Correlation coefficient: {correlation:.3f}
{self._interpret_correlation(correlation)}

*Sources: Agriculture Production Data & IMD Rainfall Data (data.gov.in)*
"""
                
                return {
                    "answer": answer,
                    "data": {
                        "crop_trend": crop_trend.to_dict(),
                        "rainfall_trend": rain_trend.to_dict(),
                        "correlation": correlation
                    },
                    "sources": ["data.gov.in - Agriculture & IMD"]
                }
        
        return {
            "answer": "⚠️ Please specify crop and region.", 
            "data": {}, 
            "sources": []
        }
    
    def _handle_general_query(self, parsed_query: Dict) -> Dict:
        """Handle general queries using LLM"""
        
        # Prepare data summary
        summary = "Available data summary:\n"
        for name, df in self.data.items():
            summary += f"\n{name}:\n{df.describe()}\n"
        
        prompt = f"""Based on this data, answer the question:

{summary}

Question: {parsed_query}

Provide a data-driven answer with specific numbers and cite sources."""

        try:
            response = self.model.generate_content(prompt)
            return {
                "answer": response.text,
                "data": {},
                "sources": ["data.gov.in datasets"]
            }
        except Exception as e:
            return {
                "answer": f"❌ Error: {e}", 
                "data": {}, 
                "sources": []
            }
    
    def _interpret_correlation(self, corr: float) -> str:
        """Interpret correlation coefficient"""
        if corr > 0.7:
            return "✅ Strong positive correlation: Higher rainfall associated with higher production."
        elif corr > 0.3:
            return "📈 Moderate positive correlation: Rainfall shows some positive influence."
        elif corr > -0.3:
            return "➡️ Weak correlation: Little relationship between rainfall and production."
        elif corr > -0.7:
            return "📉 Moderate negative correlation: Higher rainfall associated with lower production."
        else:
            return "⚠️ Strong negative correlation: Significant inverse relationship."
    
    def answer_question(self, question: str) -> Dict[str, Any]:
        """Main entry point: parse and execute query"""
        print(f"\n{'='*60}")
        print(f"🔍 Processing: {question}")
        print(f"{'='*60}")
        
        # Parse query
        parsed = self.parse_query(question)
        print(f"📋 Parsed intent: {parsed.get('intent', 'unknown')}")
        print(f"📍 States: {parsed.get('states', [])}")
        print(f"🌾 Crops: {parsed.get('crops', [])}")
        
        # Execute query
        result = self.execute_query(parsed)
        
        print(f"\n✅ Query completed!")
        print(f"{'='*60}\n")
        
        return result


if __name__ == "__main__":
    print("🌾 Project Samarth - Query Engine Test\n")
    
    # Check for API key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not found in environment")
        print("\n📝 To fix this:")
        print("1. Get API key from: https://aistudio.google.com/app/apikey")
        print("2. Create .env file with: GEMINI_API_KEY=your_key_here")
        print("3. Or set environment variable: export GEMINI_API_KEY='your_key'")
        exit(1)
    
    print(f"🔑 API Key found: {api_key[:20]}...")
    
    # Example dummy data
    rainfall_df = pd.DataFrame({
        'State': ['Punjab', 'Haryana', 'Punjab', 'Haryana'] * 3,
        'Year': [2020, 2020, 2021, 2021, 2022, 2022, 2023, 2023, 2024, 2024, 2025, 2025],
        'Annual_Rainfall_mm': [780, 620, 800, 640, 790, 630, 810, 650, 795, 635, 805, 645]
    })

    crop_df = pd.DataFrame({
        'State': ['Punjab', 'Haryana', 'Punjab', 'Haryana'] * 3,
        'District': ['Amritsar', 'Hisar', 'Ludhiana', 'Rohtak'] * 3,
        'Crop': ['Wheat', 'Wheat', 'Rice', 'Rice'] * 3,
        'Year': [2020, 2020, 2021, 2021, 2022, 2022, 2023, 2023, 2024, 2024, 2025, 2025],
        'Production': [1200, 1000, 1400, 900, 1250, 1050, 1450, 950, 1300, 1100, 1500, 1000]
    })

    data = {
        'rainfall': rainfall_df,
        'crop_production': crop_df
    }

    try:
        engine = QueryEngine(api_key=api_key, data=data)
        
        # Run test query
        question = "Compare rainfall and crop production between Punjab and Haryana."
        result = engine.answer_question(question)
        
        print("\n📊 RESULT:")
        print(result["answer"])
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
>>>>>>> 682e4b9c (Initial commit of Project Samarth)
        print("\n💡 Make sure your API key is valid!")