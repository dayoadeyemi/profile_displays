
CREATE OR REPLACE FUNCTION icount(varchar[], varchar[]) RETURNS double precision as $$
SELECT COALESCE(array_length(ARRAY(
    SELECT DISTINCT $1[i]
    FROM generate_series( array_lower($1, 1), array_upper($1, 1) ) i
    WHERE ARRAY[$1[i]] && $2
), 1) / array_length(ARRAY(
    SELECT DISTINCT UNNEST($1 || $2)
), 1)::double precision, 0);
$$ language sql;

CREATE OR REPLACE FUNCTION sim_sum(double precision, double precision, double precision, double precision) RETURNS double precision as $$
SELECT (($1*30 + $2*40+ $3*15 + $4*15)/100.0);
$$ language sql;