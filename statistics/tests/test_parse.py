import pathlib
import pytest

from tests.utils import compare_or_update_golden_with_path as cugp


def test_generate_attendance_files(
    golden_dir: pathlib.Path,
    testdata_dir: pathlib.Path,
    tmpdir: pathlib.Path,
    pytestconfig: pytest.Config,
):
    from ratfr_statistics.parse import generate_attendance_files

    source_path = testdata_dir / "attendance-statistics.csv"
    attendance_path = tmpdir / "attendance.csv"
    events_per_person_path = tmpdir / "events_per_person.csv"
    newcomer_path = tmpdir / "newcomer.csv"

    generate_attendance_files(
        source_path,
        attendance_path,
        events_per_person_path,
        newcomer_path,
        remove_source_files=False,
    )

    cugp(pytestconfig, golden_dir / "attendance.csv", attendance_path)
    cugp(
        pytestconfig,
        golden_dir / "events_per_person.csv",
        events_per_person_path,
    )
    cugp(pytestconfig, golden_dir / "newcomer.csv", newcomer_path)

