"""
PhysiqAI Workout Predictor - Comprehensive Test Harness
=======================================================
Validates the prediction model with known cases and edge cases.
"""

import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from workout_predictor_fast import OptimizedPredictor, UserProfile, WorkoutPlan, NutritionPlan


class TestHarness:
    """Comprehensive test suite for workout predictor"""

    def __init__(self):
        self.predictor = OptimizedPredictor()
        self.results = []
        self.passed = 0
        self.failed = 0

    def assert_range(self, value, min_val, max_val, description):
        """Assert value is within range"""
        if min_val <= value <= max_val:
            self.passed += 1
            return True
        else:
            self.failed += 1
            print(f"  ❌ FAIL: {description}")
            print(f"      Expected: [{min_val}, {max_val}], Got: {value}")
            return False

    def assert_positive(self, value, description):
        """Assert value is positive"""
        if value > 0:
            self.passed += 1
            return True
        else:
            self.failed += 1
            print(f"  ❌ FAIL: {description}")
            print(f"      Expected positive, Got: {value}")
            return False

    def assert_negative(self, value, description):
        """Assert value is negative"""
        if value < 0:
            self.passed += 1
            return True
        else:
            self.failed += 1
            print(f"  ❌ FAIL: {description}")
            print(f"      Expected negative, Got: {value}")
            return False

    def test_beginner_bulk(self):
        """Test beginner male bulking scenario"""
        print("\n📊 TEST: Beginner Male Bulk (12 weeks)")

        user = UserProfile(
            weight_lbs=160, height_inches=70, age=22, gender='male', body_fat_pct=12,
            training_years=0.5, training_frequency=4, sleep_hours=8, stress_level=3,
            body_type='ectomorph', smpl_betas=[0.0] * 10
        )
        workout = WorkoutPlan(
            weekly_volume_lbs=15000, sessions_per_week=4, workout_type='ppl',
            avg_intensity=0.8, progressive_overload=True
        )
        nutrition = NutritionPlan(
            daily_calories=3200, daily_protein_g=180, caloric_surplus=500, protein_timing='optimal'
        )

        result = self.predictor.predict(user, workout, nutrition, weeks=12)

        # Assertions
        self.assert_positive(result.weight_change_lbs, "Weight should increase in bulk")
        self.assert_positive(result.muscle_change_lbs, "Muscle should increase in bulk")
        self.assert_range(result.muscle_change_lbs, 3, 10, "Realistic muscle gain for beginner")
        self.assert_range(result.confidence, 0.8, 1.0, "High confidence with complete data")
        self.assert_range(len(result.new_smpl_betas), 10, 10, "Should return 10 betas")

        print(f"  ✓ Weight: {result.weight_change_lbs:+.1f} lbs")
        print(f"  ✓ Muscle: {result.muscle_change_lbs:+.1f} lbs")
        print(f"  ✓ Confidence: {result.confidence*100:.0f}%")

        return result

    def test_intermediate_cut(self):
        """Test intermediate female cutting scenario"""
        print("\n📊 TEST: Intermediate Female Cut (16 weeks)")

        user = UserProfile(
            weight_lbs=145, height_inches=65, age=28, gender='female', body_fat_pct=25,
            training_years=2.5, training_frequency=5, sleep_hours=7, stress_level=6,
            body_type='mesomorph', smpl_betas=[0.0] * 10
        )
        workout = WorkoutPlan(
            weekly_volume_lbs=12000, sessions_per_week=5, workout_type='upper_lower',
            avg_intensity=0.75, cardio_minutes_per_week=120
        )
        nutrition = NutritionPlan(
            daily_calories=1700, daily_protein_g=130, caloric_surplus=-400, protein_timing='average'
        )

        result = self.predictor.predict(user, workout, nutrition, weeks=16)

        # Assertions
        self.assert_negative(result.weight_change_lbs, "Weight should decrease in cut")
        self.assert_negative(result.fat_change_lbs, "Fat should decrease in cut")
        self.assert_range(abs(result.fat_change_lbs), 8, 20, "Realistic fat loss for 16-week cut")
        self.assert_range(result.new_body_fat_pct, 15, 22, "Healthy body fat range")

        print(f"  ✓ Weight: {result.weight_change_lbs:+.1f} lbs")
        print(f"  ✓ Fat: {result.fat_change_lbs:+.1f} lbs")
        print(f"  ✓ New BF: {result.new_body_fat_pct:.1f}%")

        return result

    def test_advanced_recomp(self):
        """Test advanced male recomposition scenario"""
        print("\n📊 TEST: Advanced Male Recomposition (20 weeks)")

        user = UserProfile(
            weight_lbs=190, height_inches=72, age=35, gender='male', body_fat_pct=18,
            training_years=8, training_frequency=6, sleep_hours=6.5, stress_level=7,
            body_type='endomorph', smpl_betas=[0.0] * 10
        )
        workout = WorkoutPlan(
            weekly_volume_lbs=20000, sessions_per_week=6, workout_type='phat',
            avg_intensity=0.85, progressive_overload=True
        )
        nutrition = NutritionPlan(
            daily_calories=2600, daily_protein_g=200, caloric_surplus=-200, protein_timing='optimal'
        )

        result = self.predictor.predict(user, workout, nutrition, weeks=20)

        # Assertions - recomposition: small muscle gain, moderate fat loss
        self.assert_range(result.muscle_change_lbs, 0, 2, "Slow muscle gain for advanced")
        self.assert_negative(result.fat_change_lbs, "Should lose fat in deficit")
        self.assert_range(result.new_body_fat_pct, 12, 17, "Leaner after recomp")

        print(f"  ✓ Weight: {result.weight_change_lbs:+.1f} lbs")
        print(f"  ✓ Muscle: {result.muscle_change_lbs:+.1f} lbs")
        print(f"  ✓ Fat: {result.fat_change_lbs:+.1f} lbs")

        return result

    def test_extreme_weight_loss(self):
        """Test extreme weight loss scenario"""
        print("\n📊 TEST: Extreme Weight Loss (24 weeks)")

        user = UserProfile(
            weight_lbs=280, height_inches=68, age=40, gender='male', body_fat_pct=35,
            training_years=0, training_frequency=3, sleep_hours=6, stress_level=8,
            body_type='endomorph', smpl_betas=[0.0] * 10
        )
        workout = WorkoutPlan(
            weekly_volume_lbs=8000, sessions_per_week=3, workout_type='full_body',
            avg_intensity=0.65, cardio_minutes_per_week=180
        )
        nutrition = NutritionPlan(
            daily_calories=2200, daily_protein_g=200, caloric_surplus=-800, protein_timing='poor'
        )

        result = self.predictor.predict(user, workout, nutrition, weeks=24)

        # Assertions
        self.assert_negative(result.weight_change_lbs, "Weight should decrease")
        self.assert_range(abs(result.weight_change_lbs), 20, 50, "Realistic extreme weight loss")
        self.assert_positive(result.muscle_change_lbs, "Beginners gain muscle even in deficit")
        self.assert_range(result.new_body_fat_pct, 20, 30, "Still healthy but improved")

        print(f"  ✓ Weight: {result.weight_change_lbs:+.1f} lbs")
        print(f"  ✓ Fat: {result.fat_change_lbs:+.1f} lbs")
        print(f"  ✓ New BF: {result.new_body_fat_pct:.1f}%")

        return result

    def test_maintenance(self):
        """Test maintenance calories scenario"""
        print("\n📊 TEST: Maintenance (12 weeks)")

        user = UserProfile(
            weight_lbs=175, height_inches=69, age=30, gender='male', body_fat_pct=15,
            training_years=3, training_frequency=4, sleep_hours=7, stress_level=5,
            body_type='mesomorph', smpl_betas=[0.0] * 10
        )
        workout = WorkoutPlan(
            weekly_volume_lbs=12000, sessions_per_week=4, workout_type='ppl',
            avg_intensity=0.75
        )
        nutrition = NutritionPlan(
            daily_calories=2600, daily_protein_g=160, caloric_surplus=0, protein_timing='average'
        )

        result = self.predictor.predict(user, workout, nutrition, weeks=12)

        # Assertions - maintenance should show minimal change
        self.assert_range(result.weight_change_lbs, -2, 2, "Minimal weight change at maintenance")
        self.assert_range(abs(result.fat_change_lbs), 0, 2, "Minimal fat change")

        print(f"  ✓ Weight: {result.weight_change_lbs:+.1f} lbs (maintenance)")

        return result

    def test_minimum_body_fat(self):
        """Test that model respects minimum body fat"""
        print("\n📊 TEST: Minimum Body Fat Constraint")

        user = UserProfile(
            weight_lbs=160, height_inches=70, age=25, gender='male', body_fat_pct=10,
            training_years=2, training_frequency=5, sleep_hours=7, stress_level=4,
            body_type='mesomorph', smpl_betas=[0.0] * 10
        )
        workout = WorkoutPlan(
            weekly_volume_lbs=15000, sessions_per_week=5, workout_type='ppl',
            avg_intensity=0.8
        )
        nutrition = NutritionPlan(
            daily_calories=1800, daily_protein_g=180, caloric_surplus=-800, protein_timing='optimal'
        )

        result = self.predictor.predict(user, workout, nutrition, weeks=16)

        # Should not go below 8% for males
        self.assert_range(result.new_body_fat_pct, 8, 12, "Should respect minimum body fat of 8%")

        print(f"  ✓ New BF: {result.new_body_fat_pct:.1f}% (enforced minimum)")

        return result

    def test_edge_case_elderly(self):
        """Test edge case: elderly trainee"""
        print("\n📊 TEST: Edge Case - Elderly Trainee (65 years)")

        user = UserProfile(
            weight_lbs=170, height_inches=68, age=65, gender='male', body_fat_pct=22,
            training_years=1, training_frequency=3, sleep_hours=6, stress_level=4,
            body_type='endomorph', smpl_betas=[0.0] * 10
        )
        workout = WorkoutPlan(
            weekly_volume_lbs=10000, sessions_per_week=3, workout_type='full_body',
            avg_intensity=0.65
        )
        nutrition = NutritionPlan(
            daily_calories=2400, daily_protein_g=150, caloric_surplus=200, protein_timing='average'
        )

        result = self.predictor.predict(user, workout, nutrition, weeks=12)

        # Age should reduce muscle gain potential
        self.assert_range(result.muscle_change_lbs, 0.5, 3, "Reduced gains due to age")

        print(f"  ✓ Muscle: {result.muscle_change_lbs:+.1f} lbs (age-adjusted)")

        return result

    def test_edge_case_very_light(self):
        """Test edge case: very light person"""
        print("\n📊 TEST: Edge Case - Very Light Female (95 lbs)")

        user = UserProfile(
            weight_lbs=95, height_inches=62, age=25, gender='female', body_fat_pct=18,
            training_years=0.5, training_frequency=3, sleep_hours=8, stress_level=3,
            body_type='ectomorph', smpl_betas=[0.0] * 10
        )
        workout = WorkoutPlan(
            weekly_volume_lbs=6000, sessions_per_week=3, workout_type='full_body',
            avg_intensity=0.7
        )
        nutrition = NutritionPlan(
            daily_calories=2200, daily_protein_g=110, caloric_surplus=300, protein_timing='optimal'
        )

        result = self.predictor.predict(user, workout, nutrition, weeks=12)

        self.assert_positive(result.weight_change_lbs, "Should gain weight")
        self.assert_range(result.weight_change_lbs, 2, 10, "Realistic for small frame")

        print(f"  ✓ Weight: {result.weight_change_lbs:+.1f} lbs")

        return result

    def run_all_tests(self):
        """Run all tests and generate report"""
        print("=" * 70)
        print("PHYSIQAI WORKOUT PREDICTOR - COMPREHENSIVE TEST HARNESS")
        print("=" * 70)

        tests = [
            self.test_beginner_bulk,
            self.test_intermediate_cut,
            self.test_advanced_recomp,
            self.test_extreme_weight_loss,
            self.test_maintenance,
            self.test_minimum_body_fat,
            self.test_edge_case_elderly,
            self.test_edge_case_very_light,
        ]

        results = []
        for test in tests:
            try:
                result = test()
                results.append({
                    'test': test.__name__,
                    'status': 'passed',
                    'weight_change': result.weight_change_lbs,
                    'muscle_change': result.muscle_change_lbs,
                    'fat_change': result.fat_change_lbs
                })
            except Exception as e:
                self.failed += 1
                print(f"  ❌ ERROR: {e}")
                results.append({'test': test.__name__, 'status': 'error', 'error': str(e)})

        # Print summary
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        print(f"Total Tests: {len(tests)}")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        print(f"Success Rate: {(self.passed / (self.passed + self.failed)) * 100:.1f}%")

        # Save report
        report = {
            'timestamp': str(__import__('datetime').datetime.now()),
            'total_tests': len(tests),
            'passed': self.passed,
            'failed': self.failed,
            'success_rate': (self.passed / (self.passed + self.failed)) * 100,
            'results': results
        }

        report_path = Path(__file__).parent / 'test_harness_report.json'
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"\nReport saved to: {report_path}")
        print("=" * 70)

        return report


def main():
    """Run test harness"""
    harness = TestHarness()
    report = harness.run_all_tests()

    # Exit with appropriate code
    if report['failed'] > 0:
        print("\n⚠️  Some tests failed")
        return 1
    else:
        print("\n✅ All tests passed!")
        return 0


if __name__ == "__main__":
    sys.exit(main())
