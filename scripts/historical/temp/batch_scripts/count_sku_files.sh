#!/bin/bash
# 统计092-110章节的SKU文件数量

echo "章节 | Facts | Skills | Eureka | 总计"
echo "------|-------|--------|--------|-----"

for i in 092 093 094 095 096 097 098 099 100 101 102 103 104 105 106 107 108 109 110; do
  facts=$(find kg/ontology/ontology-v2/chapters/chapter_$i/skus/facts -name "*.md" 2>/dev/null | wc -l)
  skills=$(find kg/ontology/ontology-v2/chapters/chapter_$i/skus/skills -name "*.md" 2>/dev/null | wc -l)
  eureka=$([ -f kg/ontology/ontology-v2/chapters/chapter_$i/eureka.md ] && echo 1 || echo 0)
  total=$((facts + skills + eureka))
  echo "$i   | $facts     | $skills      | $eureka      | $total"
done

echo ""
echo "总计："
total_facts=$(find kg/ontology/ontology-v2/chapters/chapter_*/skus/facts -name "*.md" 2>/dev/null | grep -E "chapter_(092|093|094|095|096|097|098|099|100|101|102|103|104|105|106|107|108|109|110)" | wc -l)
total_skills=$(find kg/ontology/ontology-v2/chapters/chapter_*/skus/skills -name "*.md" 2>/dev/null | grep -E "chapter_(092|093|094|095|096|097|098|099|100|101|102|103|104|105|106|107|108|109|110)" | wc -l)
total_eureka=$(ls kg/ontology/ontology-v2/chapters/chapter_{092..110}/eureka.md 2>/dev/null | wc -l)
echo "Facts: $total_facts"
echo "Skills: $total_skills"
echo "Eureka: $total_eureka"
echo "总计: $((total_facts + total_skills + total_eureka)) 个SKU文件"
