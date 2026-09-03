const apiUrl = process.env.REACT_APP_API_URL;

export async function createAuditLog({
  action,
  entityType,
  actorUserId,
  entityId,
  oldValues,
  newValues,
}) {
  try {
    await fetch(`${apiUrl}/audit-logs`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        action,
        entitytype: entityType,
        actoruserid: actorUserId,
        entityid: entityId,
        oldvalues: oldValues,
        newvalues: newValues,
      }),
    });
  } catch {
    return;
  }
}
