import json


def create_filter(n):
    cross = [[0 for _ in range(n)] for _ in range(n)]
    x_filter = [[0 for _ in range(n)] for _ in range(n)]
    mid = n // 2

    for i in range(n):
        cross[mid][i] = 1
        cross[i][mid] = 1
        x_filter[i][i] = 1
        x_filter[i][n - 1 - i] = 1

    return {"cross": cross, "x": x_filter}


filters = {}
patterns = {}

# 5x5: 2개, 13x13: 3개, 25x25: 3개
for n, case_count in [(5, 2), (13, 3), (25, 3)]:
    filter_data = create_filter(n)
    filters[f"size_{n}"] = filter_data

    for idx in range(1, case_count + 1):
        if n == 13 and idx == 3:
            # 의도적인 동점 테스트
            pattern = [[0 for _ in range(n)] for _ in range(n)]
            expected = "x"
        elif idx % 2 == 1:
            pattern = filter_data["cross"]
            expected = "+"
        else:
            pattern = filter_data["x"]
            expected = "x"

        patterns[f"size_{n}_{idx}"] = {
            "input": pattern,
            "expected": expected
        }

data = {"filters": filters, "patterns": patterns}

with open("data.json", "w", encoding="utf-8") as file:
    json.dump(data, file, indent=4, ensure_ascii=False)

print("data.json 생성 완료!")
print("필터: 5x5, 13x13, 25x25")
print("테스트 케이스:", len(patterns))
