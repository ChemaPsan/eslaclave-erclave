export function societyRateContext(session, divisionId) {
 const division = session?.scope?.divisions?.find(row => row.id === divisionId);
 const society = session?.scope?.societies?.find(row => row.id === division?.society_id);
 return society?.base_currency ? { societyId: society.id, currency: society.base_currency } : null;
}
