import json
import os
import re
import time
import math

EPSILON = 1e-9
REPEAT_COUNT = 10
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.json")


def normalize_label(label):
    if not isinstance(label, str):
        return None
    label = label.strip().lower()
    if label in ["+", "cross"]:
        return "Cross"
    if label == "x":
        return "X"
    return None


def mac(pattern, filter_matrix):
    score = 0.0
    n = len(pattern)
    for i in range(n):
        for j in range(n):
            score += pattern[i][j] * filter_matrix[i][j]
    return score


def classify(pattern, cross_filter, x_filter):
    score_cross = mac(pattern, cross_filter)
    score_x = mac(pattern, x_filter)
    if abs(score_cross - score_x) < EPSILON:
        result = "UNDECIDED"
    elif score_cross > score_x:
        result = "Cross"
    else:
        result = "X"
    return score_cross, score_x, result


def input_matrix(n, name):
    print(f"\n[{name}] {n}x{n} 행렬을 입력하세요.")
    matrix = []
    for i in range(n):
        while True:
            values = input(f"{i + 1}행 ({n}개 숫자, 공백 구분): ").split()
            if len(values) != n:
                print(f"입력 형식 오류: 각 줄에 {n}개의 숫자를 공백으로 구분해 입력하세요.")
                continue
            try:
                row = [float(value) for value in values]
                if not all(math.isfinite(value) for value in row):
                    print("유효하지 않은 숫자입니다. 다시 입력하세요.")
                    continue
                matrix.append(row)
                break
            except ValueError:
                print("숫자 입력 오류: 숫자만 입력하세요.")
    return matrix


def validate_matrix(matrix, n):
    if not isinstance(matrix, list) or len(matrix) != n:
        return False
    for row in matrix:
        if not isinstance(row, list) or len(row) != n:
            return False
        for value in row:
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                return False
            if not math.isfinite(float(value)):
                return False
    return True


def measure_one_size(n):
    pattern = [[1.0 for _ in range(n)] for _ in range(n)]
    filter_matrix = [[1.0 for _ in range(n)] for _ in range(n)]
    total_time = 0.0
    for _ in range(REPEAT_COUNT):
        start = time.perf_counter()
        mac(pattern, filter_matrix)
        end = time.perf_counter()
        total_time += end - start
    return (total_time / REPEAT_COUNT) * 1000, n * n


def print_performance():
    sizes = [3, 5, 13, 25]
    print("\n#---------------------------------------")
    print("# [3] 성능 분석 (평균/10회)")
    print("#---------------------------------------")
    print(f"{'크기':<12}{'평균 시간(ms)':<17}{'연산 횟수'}")
    print("---------------------------------------")
    for n in sizes:
        average_time, operations = measure_one_size(n)
        print(f"{n}x{n:<10}{average_time:<17.3f}{operations}")


def mode_user():
    print("\n========== 사용자 입력 모드 (3x3) ==========")
    cross_filter = input_matrix(3, "필터 A (Cross)")
    x_filter = input_matrix(3, "필터 B (X)")
    print("\n입력한 필터를 확인하세요.")
    print("Cross 필터:", cross_filter)
    print("X 필터:", x_filter)
    confirm = input("이 필터를 사용하시겠습니까? (y/n): ").strip().lower()
    if confirm != "y":
        print("필터를 다시 입력합니다.")
        return mode_user()
    pattern = input_matrix(3, "입력 패턴")
    score_cross, score_x, result = classify(pattern, cross_filter, x_filter)
    print("\n#---------------------------------------")
    print("# 판정 결과")
    print("#---------------------------------------")
    print(f"Cross 점수: {score_cross}")
    print(f"X 점수: {score_x}")
    print(f"판정 결과: {result}")
    print_performance()


def get_filter_pair(filters, n):
    filter_key = f"size_{n}"
    if filter_key not in filters:
        raise ValueError(f"{filter_key} 필터가 없습니다.")
    filter_group = filters[filter_key]
    if not isinstance(filter_group, dict):
        raise ValueError("필터 데이터 형식 오류")
    normalized_filters = {}
    for key, value in filter_group.items():
        label = normalize_label(key)
        if label is not None:
            if label in normalized_filters:
                raise ValueError(f"{label} 필터가 중복되었습니다.")
            normalized_filters[label] = value
    if "Cross" not in normalized_filters:
        raise ValueError("Cross 필터가 없습니다.")
    if "X" not in normalized_filters:
        raise ValueError("X 필터가 없습니다.")
    return normalized_filters["Cross"], normalized_filters["X"]


def mode_json():
    print("\n========== JSON 분석 모드 ==========")
    if not os.path.exists(DATA_FILE):
        print("오류: data.json 파일을 찾을 수 없습니다.")
        return
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
    except (json.JSONDecodeError, OSError) as error:
        print(f"JSON 파일 읽기 오류: {error}")
        return
    if not isinstance(data, dict):
        print("JSON 최상위 데이터 형식 오류")
        return
    filters = data.get("filters")
    patterns = data.get("patterns")
    if not isinstance(filters, dict):
        print("filters 데이터 형식 오류")
        return
    if not isinstance(patterns, dict):
        print("patterns 데이터 형식 오류")
        return

    total = passed = failed = 0
    fail_cases = []

    print("\n#---------------------------------------")
    print("# [1] 필터 로드")
    print("#---------------------------------------")
    for n in [5, 13, 25]:
        try:
            cross_filter, x_filter = get_filter_pair(filters, n)
            if not validate_matrix(cross_filter, n):
                raise ValueError("Cross 필터 크기 오류")
            if not validate_matrix(x_filter, n):
                raise ValueError("X 필터 크기 오류")
            print(f"✓ size_{n} 필터 로드 완료 (Cross, X)")
        except (ValueError, KeyError, TypeError) as error:
            print(f"✗ size_{n} 필터 로드 실패: {error}")

    print("\n#---------------------------------------")
    print("# [2] 패턴 분석 (라벨 정규화 적용)")
    print("#---------------------------------------")
    for case_id, case_data in patterns.items():
        total += 1
        try:
            match = re.fullmatch(r"size_(\d+)_(.+)", str(case_id))
            if not match:
                raise ValueError("패턴 키 형식 오류")
            n = int(match.group(1))
            if not isinstance(case_data, dict):
                raise ValueError("패턴 데이터 형식 오류")
            if "input" not in case_data:
                raise ValueError("input 항목이 없습니다.")
            if "expected" not in case_data:
                raise ValueError("expected 항목이 없습니다.")
            pattern = case_data["input"]
            expected = normalize_label(case_data["expected"])
            if expected is None:
                raise ValueError("expected 라벨 오류")
            cross_filter, x_filter = get_filter_pair(filters, n)
            if not validate_matrix(pattern, n):
                raise ValueError("패턴 크기 불일치")
            if not validate_matrix(cross_filter, n):
                raise ValueError("Cross 필터 크기 불일치")
            if not validate_matrix(x_filter, n):
                raise ValueError("X 필터 크기 불일치")
            score_cross, score_x, result = classify(pattern, cross_filter, x_filter)
            if result == expected:
                status = "PASS"
                passed += 1
                extra = ""
            else:
                status = "FAIL"
                failed += 1
                if result == "UNDECIDED":
                    extra = " (동점 규칙)"
                    reason = "동점(UNDECIDED) 처리 규칙에 따라 FAIL"
                else:
                    extra = ""
                    reason = f"예상: {expected}, 실제: {result}"
                fail_cases.append((case_id, reason))
            print(f"\n--- {case_id} ---")
            print(f"Cross 점수: {score_cross:.16f}")
            print(f"X 점수: {score_x:.16f}")
            print(f"판정: {result} | expected: {expected} | {status}{extra}")
        except (KeyError, TypeError, ValueError, OverflowError) as error:
            failed += 1
            fail_cases.append((case_id, str(error)))
            print(f"\n--- {case_id} ---")
            print(f"FAIL: {error}")

    print_performance()
    print("\n#---------------------------------------")
    print("# [4] 결과 요약")
    print("#---------------------------------------")
    print(f"총 테스트: {total}개")
    print(f"통과: {passed}개")
    print(f"실패: {failed}개")
    if fail_cases:
        print("\n실패 케이스:")
        for case_id, reason in fail_cases:
            print(f"- {case_id}: {reason}")
    else:
        print("\n모든 테스트 통과!")


def main():
    while True:
        print("\n=== Mini NPU Simulator ===")
        print("\n[모드 선택]")
        print("1. 사용자 입력 (3x3)")
        print("2. data.json 분석")
        print("0. 종료")
        choice = input("선택: ").strip()
        if choice == "1":
            mode_user()
        elif choice == "2":
            mode_json()
        elif choice == "0":
            print("프로그램을 종료합니다.")
            break
        else:
            print("잘못된 입력입니다. 다시 선택하세요.")


if __name__ == "__main__":
    main()
