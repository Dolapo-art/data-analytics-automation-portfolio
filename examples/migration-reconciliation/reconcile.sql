-- SQLite demonstration. Both input tables contain synthetic resource,count snapshots.
-- Missing values remain NULL: absence must never be confused with a zero count.
WITH resources AS (
    SELECT resource FROM source
    UNION
    SELECT resource FROM target
)
SELECT r.resource,
       s.count AS source_count,
       t.count AS target_count,
       t.count - s.count AS delta,
       CASE
           WHEN s.resource IS NULL THEN 'missing_source'
           WHEN t.resource IS NULL THEN 'missing_target'
           WHEN s.count = t.count THEN 'match'
           ELSE 'review'
       END AS review_status
FROM resources AS r
LEFT JOIN source AS s ON r.resource = s.resource
LEFT JOIN target AS t ON r.resource = t.resource
ORDER BY r.resource;
