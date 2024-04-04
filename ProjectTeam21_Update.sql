-- Update numCheckins
UPDATE Business
SET numCheckins = COALESCE((
    SELECT SUM(Count)
    FROM CheckIn
    WHERE Business.BusinessID = CheckIn.BusinessID
), 0);

-- Update reviewcount
UPDATE Business
SET ReviewCount = COALESCE((
    SELECT COUNT(*)
    FROM Review
    WHERE Business.BusinessID = Review.BusinessID
), 0);

-- Update reviewrating
UPDATE Business
SET reviewRating = COALESCE((
    SELECT AVG(Stars)
    FROM Review
    WHERE Business.BusinessID = Review.BusinessID
), 0.0);