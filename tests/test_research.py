"""Scientific checks: input quality, no future features, and honest model evaluation."""
import unittest
import numpy as np
import pandas as pd
from src.data import read_source, validate_frame, fingerprint
from src.features import derive, model_features
from src.models import prepare, run_experiment
from src.analysis import summarize


class ResearchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw, cls.audit = read_source()
        cls.experiment = run_experiment(cls.raw)

    def test_source_audit_matches_delivered_file(self):
        self.assertEqual((self.audit['source_rows'],self.audit['blank_rows_removed'],len(self.raw)),(1170,450,720))
        self.assertEqual(self.audit['first_date'],'2023-01-12')
        self.assertEqual(self.audit['last_date'],'2025-12-21')
        self.assertEqual(len(self.audit['sha256']),64)

    def test_validation_rejects_duplicate_date_and_missing_count(self):
        duplicate=pd.concat([self.raw.head(2),self.raw.head(1)],ignore_index=True)
        with self.assertRaises(ValueError):validate_frame(duplicate)
        missing=self.raw.head(2).copy();missing.loc[0,'hhs_care']=np.nan
        with self.assertRaises(ValueError):validate_frame(missing)

    def test_metric_windows_and_zero_denominator(self):
        sample=self.raw.head(20).copy();sample.loc[0,'transfers']=0
        result=derive(sample)
        self.assertTrue(pd.isna(result.loc[0,'offset_ratio']))
        self.assertTrue(result.load_mean7.iloc[:6].isna().all())
        self.assertAlmostEqual(result.load_mean7.iloc[6],result.total_load.iloc[:7].mean())
        self.assertEqual(result.net_flow.iloc[0],-sample.discharges.iloc[0])

    def test_feature_values_cannot_see_future(self):
        complete=model_features(self.raw)
        prefix=model_features(self.raw.head(300))
        pd.testing.assert_frame_equal(complete.head(300),prefix)

    def test_exact_target_dates_and_temporal_boundaries(self):
        _,pairs,_=prepare(self.raw)
        self.assertTrue(((pairs.target_date-pairs.date).dt.days==7).all())
        expected=self.raw.set_index('date').hhs_care
        for row in pairs.itertuples():self.assertEqual(row.target,expected.loc[row.target_date])
        split=self.experiment['split']
        self.assertLess(split['train_last_target'],split['validation_start'])
        self.assertLess(split['validation_last_target'],split['test_start'])
        self.assertGreaterEqual(split['test_first_origin'],split['test_start'])

    def test_selection_and_reported_error_match_predictions(self):
        experiment=self.experiment
        winner=min(experiment['scores'],key=lambda row:row['validation']['mae'])['model']
        self.assertEqual(experiment['selected_model'],winner)
        predictions=pd.DataFrame(experiment['test_predictions'])
        mae=(predictions.selected-predictions.actual).abs().mean()
        score=next(row['test']['mae'] for row in experiment['scores'] if row['model']==winner)
        self.assertAlmostEqual(mae,score,delta=.02)

    def test_fingerprint_detects_change_but_ignores_row_order(self):
        self.assertEqual(fingerprint(self.raw),fingerprint(self.raw.iloc[::-1]))
        modified=self.raw.copy();modified.loc[0,'hhs_care']+=1
        self.assertNotEqual(fingerprint(self.raw),fingerprint(modified))

    def test_sparse_data_has_no_model_claim(self):
        result=run_experiment(self.raw.head(20))
        self.assertFalse(result['available'])
        self.assertEqual(summarize(self.raw)['summary']['unobserved_days'],355)


if __name__=='__main__':unittest.main()
