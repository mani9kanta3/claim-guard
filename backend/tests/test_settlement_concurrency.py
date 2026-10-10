import threading

from app.extensions import db
from app.models import Policy, Settlement
from app.services import claim_workflow
from app.utils.errors import AppError
from tests.factories import make_claim, make_hospital, make_policy, make_user


def test_two_officers_settling_at_once_pay_only_once(app):
    customer = make_user()
    officer_one = make_user(email="one@test.com", role="OFFICER")
    officer_two = make_user(email="two@test.com", role="OFFICER")
    policy = make_policy(customer)
    claim = make_claim(policy, make_hospital(), status="APPROVED", approved_amount=30000)
    db.session.commit()

    claim_id, policy_id = claim.id, policy.id
    officer_ids = [officer_one.id, officer_two.id]
    start_together = threading.Barrier(2)
    results = []

    def settle_in_thread(officer_id):
        with app.app_context():
            start_together.wait()
            try:
                claim_workflow.settle(claim_id, officer_id)
                results.append("settled")
            except AppError as error:
                results.append(error.status_code)
            finally:
                db.session.remove()

    threads = [threading.Thread(target=settle_in_thread, args=(officer_id,)) for officer_id in officer_ids]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    db.session.expire_all()
    settlements = db.session.execute(db.select(Settlement).filter_by(claim_id=claim_id)).scalars().all()
    policy = db.session.get(Policy, policy_id)

    assert sorted(results, key=str) == [409, "settled"]
    assert len(settlements) == 1
    assert float(policy.remaining_sum_insured) == 470000
